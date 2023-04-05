import os, openai, time, datetime, sys, io

from flask import Flask, request, session, render_template, redirect, url_for, jsonify, send_file
from langchain.document_loaders import PyPDFLoader

import pandas as pd


## Local modules import
from chatbot import Chatbot
import params as prm
import cont_proc as cproc
import db_handler as dbh
from db_handler import DatabaseHandler
import oai_tool as oai

# Serve app to prod
import webbrowser
from waitress import serve
from threading import Timer

template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)),"static")

app = Flask(
    __name__, 
    template_folder=template_folder,
    static_folder=static_folder
    )


app.secret_key = os.urandom(24)


# Intitiate database if not exist
db_exist = os.path.exists(prm.DB_PATH)
if not db_exist:
    db = DatabaseHandler(prm.DB_PATH)
    db.write_db(prm.SESSION_TABLE_SQL)
    db.write_db(prm.INTERIM_CONTEXT_TABLE_SQL)
    db.write_db(prm.CONTEXT_TABLE_SQL)
    db.close_connection()
else:
    db = DatabaseHandler(prm.DB_PATH)
    db.close_connection()


# Spin up chatbot instance
chatbot = Chatbot()
print("!Chatbot initialized")


# Render welcome page
@app.route('/')
def welcome():
    db.create_connection()
    session_names = [x[0] for x in db.load_session_names()]
    db.close_connection()

    print("Available session names: ", session_names)

    return render_template('welcome.html', session_names=session_names)

@app.route('/set_session_details', methods=['POST'])
def set_session_details():
    """Set the API key, session name, upload pdf."""

    ## Get the data from the form
    # Pass API key right to the openai object
    openai.api_key = request.form['api_key']

    # Grab session names from the form
    new_session_name = request.form.get('new_session_name',0)
    existing_session_name = request.form.get('existing_session',0)

    # Determine if we deal with new or existing session
    if new_session_name != 0:
        session['NEW_SESSION'] = True
        session_name = new_session_name
    elif existing_session_name != 0:
        session['NEW_SESSION'] = False
        session_name = existing_session_name
    
    session_name = cproc.process_name(session_name)

    session['SESSION_TIME'] = str(int(time.time()))
    session['SESSION_DATE'] = datetime.datetime.fromtimestamp(time.time())
    session['SESSION_NAME'] = session_name

    

    if session['NEW_SESSION']:
        # Logic for new session. Create the session db, populate with the context 
        # and start the embedding process
        file_ = request.files['pdf']
        file_name = cproc.process_name(file_.filename)

        # Save the file to the upload folder
        saved_fname = session['SESSION_NAME'] + '_' + file_name
        fpath = os.path.join(prm.UPLOAD_FOLDER, saved_fname)
        file_.save(fpath)

        # Load the pdf process the text
        loader = PyPDFLoader(fpath)
        pages = loader.load_and_split()
        pages_df = cproc.pages_to_dataframe(pages)
        pages_refined_df = cproc.split_pages(pages_df, session['SESSION_NAME'])
        
        # Populate session and interim context table
        db.create_connection(prm.DB_PATH)
        db.insert_session(session['SESSION_NAME'], session['SESSION_DATE'])
        db.insert_context(pages_refined_df, table_name='interim_context', if_exist='replace')
        db.close_connection()

        # Get the embedding cost
        embedding_cost = round(cproc.embed_cost(pages_refined_df),4)
        # express embedding cost in dollars
        embedding_cost = f"${embedding_cost}"
        doc_length = pages_refined_df.shape[0]
        length_warning = doc_length / 60 > 1

        return render_template(
            'summary.html', 
            session_name=session_name, 
            embedding_cost=embedding_cost,
            doc_length=doc_length,
            length_warning=length_warning
            )
    
    else:
        return redirect(
            url_for('index'))


@app.route('/start_embedding', methods=['POST'])
def start_embedding():
    """Start the embedding process
    """
    # Load context data from interim table
    db.create_connection(prm.DB_PATH)
    pages_refined_df = db.load_context(session['SESSION_NAME'], table_name='interim_context')

    # Perform the embedding process here
    print('Embedding process started...')
    pages_embed_df = cproc.embed_pages(pages_refined_df)
    print('Embedding process finished.')
    ## TODO: try vectorstore to store embeddings
    pages_embed_df['embedding'] = pages_embed_df['embedding'].astype(str)
    # Prepare for future functionalities
    pages_embed_df['edges'] = None

    # insert data with embedding to main context table with if exist = append.
    db.insert_context(pages_embed_df)
    db.close_connection()

    return redirect(url_for('index'))


@app.route('/interaction')
def index():
    """render interaction main page"""

    # Load chat history
    db.create_connection(prm.DB_PATH)
    chat_history = db.load_chat_history(session['SESSION_NAME'])
    db.close_connection()

    # Convert the DataFrame to a JSON object
    chat_history_json = chat_history.to_dict(orient='records')

    if chat_history.empty:
        # If chat history is empty it means this is the first interaction
        # we need to insert the baseline exchange   
        db.create_connection(prm.DB_PATH)
        
        #insert baseline interaction
        db.insert_interaction(
            session['SESSION_NAME'], 
            'user',
            prm.SUMMARY_CTXT_USR
        )
        db.insert_interaction(
            session['SESSION_NAME'], 
            'assistant',
            prm.SUMMARY_TXT_ASST
        )
        db.close_connection()

    return render_template(
        'index.html',
        session_name=session['SESSION_NAME'],
        chat_history=chat_history_json
        )



@app.route('/ask', methods=['POST'])
def ask():
    """handle POST request from the form and return the response"""
    data = request.get_json()
    question = data['question']


    # Handle chat memory and context
    print('Handling chat memory and context...')
    db.create_connection(prm.DB_PATH)
    # Get the context table
    recall_table = db.load_context(session['SESSION_NAME'])
    db.close_connection()

    ## Chop recall table to only include contexts for sources, user, or assistant
    src_f = (recall_table['interaction_type'] == 'source')
    usr_f = (recall_table['interaction_type'] == 'user') & (recall_table['timestamp']!=0)
    ast_f = (recall_table['interaction_type'] == 'assistant') & (recall_table['timestamp']!=0)
    
    recall_table_source = recall_table[src_f]
    recall_table_user = recall_table[usr_f]
    recall_table_assistant = recall_table[ast_f]

    # TODO: make a function in cproc out of that!!!
    recal_embed_source = cproc.convert_table_to_dct(recall_table_source)
    recal_embed_user = cproc.convert_table_to_dct(recall_table_user)
    recal_embed_assistant = cproc.convert_table_to_dct(recall_table_assistant)

    ## Get the context from recall table that is the most similar to user input
    num_samples = prm.NUM_SAMPLES
    if recall_table_source.shape[0] < prm.NUM_SAMPLES:
        num_samples = recall_table_source.shape[0]
        print('WARNING! Source material is shorter than number of samples you want to get. Setting number of samples to the number of source material sections.')

    ## Get SRC context
    if len(recal_embed_source) == 0:
        recal_source = 'No context found'
        print('WARNING! No source material found.')
        idxs=[]
    else:
        recal_source_id = oai.order_document_sections_by_query_similarity(question, recal_embed_source)[0:num_samples]
        # If recal source id is a list, join the text from the list
        if len(recal_source_id)>1:
            idxs = [x[1] for x in recal_source_id]
            recal_source = recall_table.loc[idxs]['text'].to_list()
            recal_source = '| '.join(recal_source)
        else: 
            idxs = recal_source_id[1]
            recal_source = recall_table.loc[idxs]['text']

    ## GET QRY context
    if len(recal_embed_user) == 0:
        recal_user = 'No context found'
    else:
        recal_user_id = oai.order_document_sections_by_query_similarity(question, recal_embed_user)[0][1]
        recal_user = recall_table.loc[recal_user_id]['text']

    ## GET RPL context
    if len(recal_embed_assistant) == 0:
        recal_assistant = 'No context found'
    else:
        recal_assistant_id = oai.order_document_sections_by_query_similarity(question, recal_embed_assistant)[0][1]
        recal_assistant = recall_table.loc[recal_assistant_id]['text']


    # Look for assistant and user messages in the interaction table that have the latest timestamp
    last_usr_max = recall_table_user['timestamp'].astype(int).max()
    last_asst_max = recall_table_assistant['timestamp'].astype(int).max()
    if last_usr_max == 0:
        latest_user = 'No context found'
    else:
        latest_user = recall_table_user[recall_table_user['timestamp']==last_usr_max]['text']

    if last_asst_max == 0:
        latest_assistant = 'No context found'
    else:
        latest_assistant = recall_table_assistant[recall_table_assistant['timestamp']==last_asst_max]['text']

    print('Done handling chat memory and context.')
    
    ## Grab chapter name if it exists, otherwise use session name
    ## It will become handy when user wants to know from which chapter the context was taken

    if len(idxs)>1:
        recal_source_pages = recall_table.loc[idxs]['page'].to_list()
    elif len(idxs)==1:
        recal_source_pages = recall_table.loc[idxs]['page']
    else:
        recal_source_pages = 'No context found'

    print(f'I will answer your question basing on the following context: {set(recal_source_pages)}')


    message = chatbot.build_prompt(
        latest_user,
        latest_assistant,
        recal_source,
        recal_user,
        recal_assistant,
        question
        )
    print("!Prompt built")

    # Grab call user content from messages alias
    usr_message_content = message[0]['content']
    # Count number of tokens in user message and display it to the user
    token_passed = oai.num_tokens_from_messages(message)
    context_capacity =  4096 - token_passed
    print(f"Number of tokens passed to the model: {token_passed}")
    print(f"Number of tokens left in the context: {context_capacity}")


    # generate response
    response = chatbot.chat_completion_response(message)
    print("!Response generated")


    # Open DB so the assistant can remember the conversation
    session['SPOT_TIME'] = str(int(time.time()))
    db.create_connection()
    # Insert user message into DB so we can use it for another user's input
    db.insert_interaction(
        session['SESSION_NAME'], 
        'user',
        question,
        timestamp=session['SPOT_TIME']
    )
    db.insert_interaction(
        session['SESSION_NAME'], 
        'assistant',
        response['choices'][0]['message']['content'],
        timestamp=response['created']
    )
    db.close_connection()

    return jsonify({'response': response})


# TBC => implement dbhandler from here ###################
@app.route('/export_interactions', methods=['GET'])
def export_interactions():
    """Export the interaction table as a JSON file for download.
    """

    # Connect to the database
    db.create_connection()
    # Retrieve the interaction table
    recall_df = db.load_context(session['SESSION_NAME'])
    db.close_connection()
    # remove records that are user or assistant interaction type and have 
    # time signature 0 - these were injected into the table as a seed to 
    # improve performance of the model at the beginning of the conversation
    seed_f = (
        (recall_df['interaction_type'].isin(['user','assistant'])) & (recall_df['timestamp'] == 0)
        )
    recall_df = recall_df[~seed_f]

    # Convert the DataFrame to a JSON string
    interactions_json = recall_df.to_json(orient='records', indent=2)

    # Create a file-like buffer to hold the JSON string
    json_buffer = io.BytesIO()
    json_buffer.write(interactions_json.encode('utf-8'))
    json_buffer.seek(0)

    # Send the JSON file to the user for download
    return send_file(
        json_buffer, 
        as_attachment=True, 
        download_name=f"interactions_{session['SESSION_NAME']}.json", 
        mimetype='application/json')


def open_browser():
    """Open default browser to display the app."""
    webbrowser.open_new('http://127.0.0.1:5000/')


if __name__ == '__main__':
    # Run DEV server
    # app.run(debug=True, host='0.0.0.0', port=5001)

    # run PROD server
    Timer(1, open_browser).start()
    serve(app, host='0.0.0.0', port=5000)