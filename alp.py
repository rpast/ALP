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


# Render welcome page
@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/set_session_details', methods=['POST'])
def set_session_details():
    """Set the API key, session name, upload pdf."""

    ## Get the data from the form
    # Pass API key right to the openai object
    with open(os.path.join(static_folder, 'data/apikey.txt'), 'r') as f:
        openai.api_key = f.read()
    # openai.api_key = request.form['api_key']

    session_name = request.form['session_name']
    file = request.files['pdf']

    # make sure names are correctly formatted
    session_name = cproc.process_name(session_name)
    file_name = cproc.process_name(file.filename)

    # Pre-process uploaded source file, create the session db and save
    session['SESSION_TIME'] = str(int(time.time()))
    session['SESSION_DATE'] = datetime.datetime.fromtimestamp(time.time())
    session['SESSION_NAME'] = session_name

    # Save the file to the upload folder
    saved_fname = session['SESSION_NAME'] + '_' + file_name
    fpath = os.path.join(prm.UPLOAD_FOLDER, saved_fname)
    file.save(fpath)

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


# TBC => implement dbhandler from here ###################
@app.route('/start_embedding', methods=['POST'])
def start_embedding():
    """Start the embedding process
    """
    # Load context data from db
    conn = dbh.create_connection(session['DB_PTH'])
    pages_refined_df = pd.read_sql_query(f"SELECT * FROM context_{session['DB_CODE']}", conn)
    ## db OOP refactor: load data from interim context table

    # Perform the embedding process here
    pages_embed_df = cproc.embed_pages(pages_refined_df)
    ## db OOP refactor: use BLOB to store embedding data
    pages_embed_df['embedding'] = pages_embed_df['embedding'].astype(str)

    ## db OOP refactor: insert data with embedding to main context table with if exist = append. Add edges column to the table.
    # Create context table
    dbh.insert_context(conn, session['DB_CODE'], pages_embed_df)

    conn.close()

    return redirect(url_for('index'))


@app.route('/interaction')
def index():
    """render interaction main page"""

    # Create interaction table
    conn = dbh.create_connection(session['DB_PTH'])
    dbh.create_table(conn, f"CREATE TABLE IF NOT EXISTS interaction_{session['DB_CODE']} (session_name, interaction_type, text, embedding, num_tokens_oai, time_signature)")

    # Seed the interaction table with the context
    dbh.bulk_insert_interaction(
    conn, 
    prm.SUMMARY_CTXT_USR, 
    prm.SUMMARY_TXT_ASST, 
    session['DB_CODE']
    )
    conn.close()    

    return render_template('index.html')


@app.route('/ask', methods=['POST'])
def ask():
    """handle POST request from the form and return the response"""
    data = request.get_json()
    question = data['question']


    # Handle chat memory and context
    conn = dbh.create_connection(session['DB_PTH'])
    recal_table = dbh.fetch_recall_table(session['DB_CODE'], conn)
    conn.close() 
    ## Chop recall table to only include contexts for sources, user, or assistant
    recal_table_source = recal_table[recal_table['interaction_type'] == 'source']
    recal_table_user = recal_table[recal_table['interaction_type'] == 'user']
    recal_table_assistant = recal_table[recal_table['interaction_type'] == 'assistant']

    recal_embed_source = cproc.convert_table_to_dct(recal_table_source)
    recal_embed_user = cproc.convert_table_to_dct(recal_table_user)
    recal_embed_assistant = cproc.convert_table_to_dct(recal_table_assistant)

    ## Get the context from recall table that is the most similar to user input
    num_samples = prm.NUM_SAMPLES
    if recal_table_source.shape[0] < prm.NUM_SAMPLES:
        num_samples = recal_table_source.shape[0]
        print('Source material is shorter than number of samples you want to get. Setting number of samples to the number of source material sections.')

    ## Get SRC context
    if len(recal_embed_source) == 0:
        recal_source = 'No context found'
    else:
        recal_source_id = oai.order_document_sections_by_query_similarity(question, recal_embed_source)[0:num_samples]
        # If recal source id is a list, join the text from the list
        if len(recal_source_id)>1:
            idxs = [x[1] for x in recal_source_id]
            recal_source = recal_table.loc[idxs]['text'].to_list()
            recal_source = '| '.join(recal_source)
        else: 
            recal_source = recal_table.loc[recal_source_id[1]]['text']
    ## GET QRY context
    if len(recal_embed_user) == 0:
        recal_user = 'No context found'
    else:
        recal_user_id = oai.order_document_sections_by_query_similarity(question, recal_embed_user)[0][1]
        recal_user = recal_table.loc[recal_user_id]['text']
    ## GET RPL context
    if len(recal_embed_assistant) == 0:
        recal_assistant = 'No context found'
    else:
        recal_assistant_id = oai.order_document_sections_by_query_similarity(question, recal_embed_assistant)[0][1]
        recal_assistant = recal_table.loc[recal_assistant_id]['text']


    # Look for assistant and user messages in the interaction table that have the latest time_signature
    last_usr_max = recal_table_user['time_signature'].astype(int).max()
    last_asst_max = recal_table_assistant['time_signature'].astype(int).max()
    if last_usr_max == 0:
        latest_user = 'No context found'
    else:
        latest_user = recal_table_user.loc[recal_table_user['time_signature']==str(last_usr_max)]['text'].values[0]

    if last_asst_max == 0:
        latest_assistant = 'No context found'
    else:
        latest_assistant = recal_table_assistant.loc[recal_table_assistant['time_signature']==str(last_asst_max)]['text'].values[0]
    
    ## Grab chapter name if it exists, otherwise use session name
    ## It will become handy when user wants to know from which chapter the context was taken
    if len(idxs)>1:
        recal_source_pages = recal_table.loc[idxs]['page'].to_list()
    else:
        recal_source_pages = recal_table.loc[recal_source_id[1]]['page']

    print(f'I will answer your question basing on the following context: {set(recal_source_pages)}')

    # initialize classes
    chatbot = Chatbot()
    print("!Chatbot initialized")

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
    conn = dbh.create_connection(session['DB_PTH'])
    # Insert user message into DB so we can use it for another user's input
    dbh.insert_interaction(
        conn, 
        session['DB_CODE'], 
        'user', 
        question,
        session['SPOT_TIME']
        )
    # Insert model's response into DB so we can use it for another user's input
    dbh.insert_interaction(
        conn,
        session['DB_CODE'],
        'assistant',
        response['choices'][0]['message']['content'],
        response['created']
        )
    conn.close()


    return jsonify({'response': response})


@app.route('/export_interactions', methods=['GET'])
def export_interactions():
    """Export the interaction table as a JSON file for download.
    """

    # Connect to the database
    conn = dbh.create_connection(session['DB_PTH'])
    # Retrieve the interaction table
    recall_df = dbh.fetch_recall_table(session['DB_CODE'], conn)
    conn.close()
    # remove records that are user or assistant interaction type and have time signature 0 - these were injected into the table as a seed to improve performance of the model at the beginning of the conversation
    seed_f = (
        (recall_df['interaction_type'].isin(['user','assistant'])) & (recall_df['time_signature'] == '0')
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
        download_name=f"interactions_{session['DB_CODE']}.json", 
        mimetype='application/json')


def open_browser():
    """Open default browser to display the app."""
    webbrowser.open_new('http://127.0.0.1:5000/')


if __name__ == '__main__':
    # Run DEV server
    app.run(debug=True, host='0.0.0.0', port=5000)

    #run PROD server
    # Timer(1, open_browser).start()
    # serve(app, host='0.0.0.0', port=5000)