import os, openai, time, datetime, json
import pandas as pd

from flask import Flask, request, session, render_template, redirect, url_for, jsonify

from langchain.document_loaders import PyPDFLoader

from chatbot import Chatbot
import params as prm
import cont_proc as cproc
import db_handler as dbh
import oai_tool as oai



app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = prm.UPLOAD_FOLDER

now = time.time()
date = datetime.datetime.fromtimestamp(now)
app.config['TIME'] = str(int(now))
app.config['DATE'] = date





# Render welcome page
@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/set_session_details', methods=['POST'])
def set_session_details():
    """Set the API key, session name, upload pdf."""

    # get the data from the form
    api_key = request.form['api_key']
    session_name = request.form['session_name']
    file = request.files['pdf']

    # Create the db and file codes + save the file
    session['DB_CODE'] = session_name + '_' + app.config['TIME']

    file_name = session['DB_CODE'] + '_' + file.filename.lower().strip().replace(' ', '_')
    fpath = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    file.save(fpath)

    # Load the pdf and split it into pages
    loader = PyPDFLoader(fpath)
    pages = loader.load_and_split()

    # Process the pages and save to dbx
    pages_df = cproc.pages_to_dataframe(pages)
    pages_refined_df = cproc.split_pages(pages_df, session['DB_CODE'])
    
    # Create session table
    conn = dbh.create_connection(f"{session['DB_CODE']}.db")
    dbh.create_table(conn, prm.SESSION_TABLE_SQL)
    dbh.insert_session(conn, session['DB_CODE'], app.config['DATE'])
    dbh.insert_context(conn, session['DB_CODE'], pages_refined_df)
    conn.close()

    openai.api_key = api_key

    embedding_cost = cproc.embed_cost(pages_refined_df)

    return render_template(
        'summary.html', 
        session_name=session_name, 
        embedding_cost=embedding_cost
        )


@app.route('/start_embedding', methods=['POST'])
def start_embedding():
    # Load context data from db
    conn = dbh.create_connection(f"{session['DB_CODE']}.db")
    pages_refined_df = pd.read_sql_query(f"SELECT * FROM context_{session['DB_CODE']}", conn)

    # Perform the embedding process here
    pages_embed_df = cproc.embed_pages(pages_refined_df)
    pages_embed_df['embedding'] = pages_embed_df['embedding'].astype(str)

    # Create context table
    dbh.insert_context(conn, session['DB_CODE'], pages_embed_df)
    conn.close()

    return redirect(url_for('index'))


@app.route('/interaction')
def index():
    """render interaction main page"""

    # Create interaction table
    conn = dbh.create_connection(f"{session['DB_CODE']}.db")
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
    conn = dbh.create_connection(f"{session['DB_CODE']}.db")
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
    conn = dbh.create_connection(f"{session['DB_CODE']}.db")
    # Insert user message into DB so we can use it for another user's input
    dbh.insert_interaction(
        conn, 
        session['DB_CODE'], 
        'user', 
        question,
        app.config['TIME']
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



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)