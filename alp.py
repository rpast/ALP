import os
import io
import re
import time
import openai
import datetime
import ast
import pandas as pd

from flask import Flask, request, session, render_template, redirect, url_for, jsonify, send_file
from langchain.document_loaders import PyPDFLoader

## Local modules import
from chatbot import Chatbot
import params as prm
import cont_proc as cproc
from db_handler import DatabaseHandler
import oai_tool as oai

# Serve app to prod
import webbrowser
from waitress import serve
from threading import Timer


# Set up paths
template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)),"static")


# Initiate Flask app
app = Flask(
    __name__, 
    template_folder=template_folder,
    static_folder=static_folder
    )

app.secret_key = os.urandom(24)

## Load key from api_key.txt THIS IS FOR DEV ONLY
with open('/home/nf/Documents/projekty/ai_apps/ALP/ALP/static/data/api_key.txt') as f:
    key_ = f.read()
    openai.api_key = key_


# Intitiate database if not exist
db_exist = os.path.exists(prm.DB_PATH)
if not db_exist:
    with DatabaseHandler(prm.DB_PATH) as db:
        db.write_db(prm.SESSION_TABLE_SQL)
        # db.write_db(prm.INTERIM_COLLECTIONS_TABLE_SQL)
        db.write_db(prm.COLLECTIONS_TABLE_SQL)
        db.write_db(prm.CHAT_HIST_TABLE_SQL)
        db.write_db(prm.EMBEDDINGS_TABLE_SQL)

# Spin up chatbot instance
chatbot = Chatbot()
print("!Chatbot initialized")


# Render home page
@app.route('/')
def home():

    return render_template(
        'home.html'
        )

@app.route('/collection_manager', methods=['GET', 'POST'])
def collection_manager():
    # TODO: fetch collections from database and pass them so they can be displayed
    return render_template(
            'collection_manager.html'
            )

# create /process_collection route
@app.route('/process_collection', methods=['POST'])
def process_collection():
    """Process collection
    Process the collection of documents.
    """
    print("!Processing collection")
    db = DatabaseHandler(prm.DB_PATH)

    # Get the data from the form
    collection_name = request.form['collection_name']
    collection_name = cproc.process_name(collection_name)
    print(f"!Collection name: {collection_name}")

    # Process the collection
    file_ = request.files['pdf']
    file_name = cproc.process_name(file_.filename)
    collection_source = file_name
    print(f"!Collection source: {collection_source}")

    # Save the file to the upload folder
    saved_fname = collection_name + '_' + file_name
    fpath = os.path.join(prm.UPLOAD_FOLDER, saved_fname)
    file_.save(fpath)
    print(f"!File saved to: {fpath}")

    # Load the pdf & process the text
    loader = PyPDFLoader(fpath) # langchain simple pdf loader
    pages = loader.load_and_split() # split by pages

    # Process text data further so it fits the context mechanism
    pages_df = cproc.pages_to_dataframe(pages)
    pages_refined_df = cproc.split_pages(pages_df, collection_name)

    # Add UUIDs to the dataframe!
    pages_refined_df['uuid'] = cproc.create_uuid()
    pages_refined_df['doc_uuid'] = [cproc.create_uuid() for x in range(pages_refined_df.shape[0])]


    # TODO: Switch to Hugging Face API with embedding model
    # Get the embedding cost
    embedding_cost = round(cproc.embed_cost(pages_refined_df),4)
    # express embedding cost in dollars
    embedding_cost = f"${embedding_cost}"
    doc_length = pages_refined_df.shape[0]
    length_warning = doc_length / 60 > 1
    print(f"!Embedding cost: {embedding_cost}")

    if length_warning != True:
        # Perform the embedding process here
        print('Embedding process started...')
        pages_embed_df = cproc.embed_pages(pages_refined_df)
        print('Embedding process finished.')
        ## TODO: use vectorstore to store embeddings
        pages_embed_df['embedding'] = pages_embed_df['embedding'].astype(str)

        ## DMODEL UPDATE
        ## Decouple context from embeddings
        ## TODO: implement UUID for context
        to_serialize_df = pages_embed_df[['name', 'embedding']]
        embed_df = cproc.serialize_embedding(to_serialize_df)
        #######################

        # insert data with embedding to main context table with if exist = append.
        with db as db_conn:
            db_conn.insert_context(pages_embed_df)
        
        print('!Embedding process finished. Collection saved to database.')
        
    return render_template(
            'collection_manager.html'
            )

# Create /session_manager route
@app.route('/session_manager', methods=['GET', 'POST'])
def session_manager():
    """Session manager
    Manage sessions.
    """
    db = DatabaseHandler(prm.DB_PATH)

    # Load session names from the database
    with db as db_conn:
        # We want to see available sessions
        if db_conn.load_session_names() is not None:
            session_names = [x[0] for x in db_conn.load_session_names()]
            session_ids = [x[1] for x in db_conn.load_session_names()]

            # extract from session dates only the date YYYY-MM-DD
            # session_dates = [x.split()[0] for x in session_dates]

            sessions = list(zip(session_names, session_ids))
        else:
            sessions = []
        
        # We want to see available collections
        # TODO: make a method out of that
        subs = ['name','uuid']
        collections_table = pd.read_sql('SELECT * FROM collections', db_conn.conn)[subs]
        collections = collections_table.drop_duplicates(subset=subs)
        # return list of tuples from collections
        collections = [tuple(x) for x in collections.values]

    return render_template(
            'session_manager.html',
            sessions=sessions,
            collections=collections
            )

#Create /process_session
@app.route('/process_session', methods=['POST'])
def process_session():
    """Process session
    Set the API key, session name, connect sources for new session.
    """

    session['UUID'] = cproc.create_uuid()
    session['SESSION_DATE'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db = DatabaseHandler(prm.DB_PATH)

    ## Get the data from the form
    # Pass API key right to the openai object
    # openai.api_key = request.form['api_key']


    #determine if use clicked session_create or session_start
    session_action = request.form.get('session_action', 0)

    # Determine if we deal with new or existing session
    # And handle session variables accordingly
    if session_action == 'Create':
        session_name = request.form.get('new_session_name', 0)

        session['SESSION_NAME'] = cproc.process_name(session_name)

    elif session_action == 'Start':
        name_grabbed = request.form.getlist('existing_session_name')
        sesion_id = [ast.literal_eval(x)[1] for x in name_grabbed][0]
        name = [ast.literal_eval(x)[0] for x in name_grabbed][0]
        print('Starting existing session: ', name)
        session['SESSION_NAME'] = name
        session['UUID'] = sesion_id


    if session_action == 'Create':
        print('Creating new session: ', session['SESSION_NAME'])

        # grab collections from the form
        collections = request.form.getlist('collections')

        collection_ids = [ast.literal_eval(x)[1] for x in collections]
        for collection_uuid in collection_ids:
            db.insert_session(
                session['UUID'],
                collection_uuid,
                session['SESSION_NAME'],
                session['SESSION_DATE']
            )

        return redirect(
            url_for('index'))
    

    elif session_action == 'Start':
        print('Starting existing: ', session['SESSION_NAME'])
        # proceed to interaction
        return redirect(
            url_for('index'))


@app.route('/interaction')
def index():
    """render interaction main page"""
    
    ## DOING
    ## Use UUIDs instead of names
    ## Check what is wrong with chat history seed in if chat_history.empty

    db = DatabaseHandler(prm.DB_PATH)

    # Load chat history
    with db as db_conn:
        chat_history = db_conn.load_context(
            [session['UUID']], 
            table_name='chat_history'
            )


    if chat_history.empty:
        # If chat history is empty it means this is the first interaction
        # we need to insert the baseline exchange   
        
        with db as db_conn:
            #insert baseline interaction
            db_conn.insert_interaction(
                session['UUID'],
                'user',
                prm.SUMMARY_CTXT_USR
            )
            db_conn.insert_interaction(
                session['UUID'],
                'assistant',
                prm.SUMMARY_TXT_ASST
            )

    # Convert the DataFrame to a JSON object
    chat_history_json = chat_history.to_dict(orient='records')
        
    return render_template(
        'index.html',
        session_name=session['SESSION_NAME'],
        session_date=session['SESSION_DATE'],
        chat_history=chat_history_json
        )


@app.route('/ask', methods=['POST'])
def ask():
    """handle POST request from the form and return the response
    """

    db = DatabaseHandler(prm.DB_PATH)

    data = request.get_json()
    question = data['question']

    # Handle chat memory and context
    print('Handling chat memory and context...')
    
    with db as db_conn:
        # Form recall tables
        collections = db_conn.load_collections(session['UUID'])
        recall_table_context = db_conn.load_context(collections)
        recall_table_chat = db_conn.load_context([session['UUID']], table_name='chat_history')
    

    ## Chop recall table to only include contexts for sources, user, or assistant
    # src_f = (recall_table['interaction_type'] == 'source')
    usr_f = (recall_table_chat['interaction_type'] == 'user') & (recall_table_chat['timestamp']!=0)
    ast_f = (recall_table_chat['interaction_type'] == 'assistant') & (recall_table_chat['timestamp']!=0)
    
    # recall_table_source = recall_table[src_f]
    recall_table_source = recall_table_context
    recall_table_user = recall_table_chat[usr_f]
    recall_table_assistant = recall_table_chat[ast_f]

    # TODO: make a function in cproc out of that!!!
    recal_embed_source = cproc.convert_table_to_dct(recall_table_source)
    recal_embed_user = cproc.convert_table_to_dct(recall_table_user)
    recal_embed_assistant = cproc.convert_table_to_dct(recall_table_assistant)

    # TODO: this should be a chatbot method
    ## Get the context from recall table that is the most similar to user input
    num_samples = prm.NUM_SAMPLES # <- this defines how many samples we want to get from the source material
    if recall_table_source.shape[0] < prm.NUM_SAMPLES:
        # This should happen for short documents otherwise this suggests a bug (usually with session name)
        num_samples = recall_table_source.shape[0]
        print('WARNING! Source material is shorter than number of samples you want to get. Setting number of samples to the number of source material sections.')

    ## Get SRC context
    if len(recal_embed_source) == 0:
        recal_source = 'No context found'
        print('WARNING! No source material found.')
        idxs=[]
    else:
        # Get the context most relevant to user's question
        recal_source_id = oai.order_document_sections_by_query_similarity(question, recal_embed_source)[0:num_samples]
        if len(recal_source_id)>1:
            # If recal source id is a list n>1, join the text from the list
            idxs = [x[1] for x in recal_source_id]
            recal_source = recall_table_context.loc[idxs]['text'].to_list()
            recal_source = '| '.join(recal_source)
        else: 
            # Otherwise just get the text from the single index
            idxs = recal_source_id[1]
            recal_source = recall_table_context.loc[idxs]['text']

    ## GET QRY context
    # We get most relevant context from the user's previous messages here
    if len(recal_embed_user) == 0:
        recal_user = 'No context found in user chat history'
    else:
        recal_user_id = oai.order_document_sections_by_query_similarity(question, recal_embed_user)[0][1]
        recal_user = recall_table_chat.loc[recal_user_id]['text']

    ## GET RPL context
    # We get most relevant context from the agent's previous messages here
    if len(recal_embed_assistant) == 0:
        recal_agent = 'No context found agent chat history'
    else:
        recal_agent_id = oai.order_document_sections_by_query_similarity(question, recal_embed_assistant)[0][1]
        recal_agent = recall_table_chat.loc[recal_agent_id]['text']


    # Look for agent and user messages in the interaction table that have the latest timestamp
    # We will put them in the context too.
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
    
    ## Grab the page number from the recall table
    ## It will become handy when user wants to know from which chapter the context was taken

    if len(idxs)>1:
        recall_source_pages = recall_table_context.loc[idxs]['page'].to_list()
    elif len(idxs)==1:
        recall_source_pages = recall_table_context.loc[idxs]['page']
    else:
        recall_source_pages = 'No context found'

    print(f'I will answer your question basing on the following context: {set(recall_source_pages)}')


    # Build prompt
    message = chatbot.build_prompt(
        latest_user,
        latest_assistant,
        recal_source,
        recal_user,
        recal_agent,
        question
        )
    print("!Prompt built")


    # Grab call user content from messages alias
    usr_message_content = message[0]['content']

    # Count number of tokens in user message and display it to the user
    # TODO: flash it on the front-end
    token_passed = oai.num_tokens_from_messages(message)
    context_capacity =  4096 - token_passed
    print(f"Number of tokens passed to the model: {token_passed}")
    print(f"Number of tokens left in the context: {context_capacity}")


    # generate response
    response = chatbot.chat_completion_response(message)
    print("!Response generated")


    # save it all to DB so the agent can remember the conversation
    session['SPOT_TIME'] = str(int(time.time()))
    with db as db_conn:
        # Insert user message into DB so we can use it for another user's input
        db_conn.insert_interaction(
            session['UUID'],
            'user',
            question,
            timestamp=session['SPOT_TIME']
        )
        db_conn.insert_interaction(
            session['UUID'],
            'assistant',
            response['choices'][0]['message']['content'],
            timestamp=response['created']
        )

    return jsonify({'response': response})


@app.route('/export_interactions', methods=['GET'])
def export_interactions():
    """Export the interaction table as a JSON file for download.
    """

    db = DatabaseHandler(prm.DB_PATH)
    
    # Connect to the database
    with db as db_conn:
        # Retrieve the interaction table
        recall_df = db_conn.load_context(session['UUID'], table_name='chat_history')

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


# This rout is obsolete
# @app.route('/proc_session', methods=['POST'])
# def proc_session():
#     """Process session
#     Set the API key, session name, connect sources for new session.
#     """

#     db = DatabaseHandler(prm.DB_PATH)

#     ## Get the data from the form
#     # Pass API key right to the openai object
#     # openai.api_key = request.form['api_key']

#     ## Load key from api_key.txt
#     with open('/home/nf/Documents/projekty/ai_apps/ALP/ALP/static/data/api_key.txt') as f:
#         key = f.read()
#         openai.api_key = key

#     # Grab session names from the form
#     new_session_name = request.form.get('new_session_name',0)
#     existing_session_name = request.form.get('existing_session',0)

#     # Determine if we deal with new or existing session
#     if new_session_name != 0:
#         session['NEW_SESSION'] = True
#         session_name = new_session_name
#         session_date = datetime.datetime.fromtimestamp(time.time())
#     elif existing_session_name != 0:
#         session['NEW_SESSION'] = False
#         # session name and date comes as string. We need to extract them.
#         pattern = r"'(.*?)'"
#         existing_session_details = re.findall(pattern, existing_session_name)
#         session_name = existing_session_details[0]
#         session_date = existing_session_details[1]

#     # Make sure the session name is formatted correctly
#     session_name = cproc.process_name(session_name)

#     # Set session variables
#     session['SESSION_TIME'] = str(int(time.time()))
#     session['SESSION_DATE'] = str(session_date).split()[0]
#     session['SESSION_NAME'] = session_name
#     session['UUID'] = cproc.create_uuid()


#     # New session has specific rules
#     if session['NEW_SESSION']:
#         # Logic for new session. 
#         # Insert session details to session table, populate the context table
#         # kick-off the embedding process
#         file_ = request.files['pdf']
#         file_name = cproc.process_name(file_.filename)
#         session['SESSION_SOURCE'] = file_name


#         # Save the file to the upload folder
#         saved_fname = session['SESSION_NAME'] + '_' + file_name
#         fpath = os.path.join(prm.UPLOAD_FOLDER, saved_fname)
#         file_.save(fpath)

#         # Load the pdf & process the text
#         loader = PyPDFLoader(fpath) # langchain simple pdf loader
#         pages = loader.load_and_split() # split by pages

#         # Process text data further so it fits the context mechanism
#         pages_df = cproc.pages_to_dataframe(pages)
#         pages_refined_df = cproc.split_pages(pages_df, session['SESSION_NAME'])
        
#         # Get the embedding cost
#         embedding_cost = round(cproc.embed_cost(pages_refined_df),4)
#         # express embedding cost in dollars
#         embedding_cost = f"${embedding_cost}"
#         doc_length = pages_refined_df.shape[0]
#         length_warning = doc_length / 60 > 1

#         ## DMODEL IMPLEMENTATION
#         # create uuid for the collection and for each text instance
#         session['COLLECTION_UUID'] = cproc.create_uuid()
#         pages_refined_df['doc_uuid'] = [cproc.create_uuid() for x in range(pages_refined_df.shape[0])] 
#         pages_refined_df['uuid'] = session['COLLECTION_UUID']

#         # Populate session and interim context table
#         with db as db_conn:
#             db_conn.insert_session(
#                 session['UUID'],
#                 'collection uuid',
#                 'chat uuid',
#                 session['SESSION_NAME'], 
#                 session['SESSION_DATE'], 
#                 session['SESSION_SOURCE']
#                 )
#             db_conn.insert_context(
#                 pages_refined_df, 
#                 table_name='interim_collections', 
#                 if_exist='replace'
#                 )
    

#         return render_template(
#             'summary.html', 
#             session_uuid=session['UUID'],
#             session_name=session_name, 
#             embedding_cost=embedding_cost,
#             doc_length=doc_length,
#             length_warning=length_warning
#             )
    
#     # If we deal with existing session 
#     # Proceed to the chatbot
#     else:
#        return redirect(
#             url_for('index'))


# @app.route('/start_embedding', methods=['POST'])
# def start_embedding():
#     """Start the embedding process
#     """

#     db = DatabaseHandler(prm.DB_PATH)

#     # Load context data from interim table
#     with db as db_conn:
#         pages_refined_df = db_conn.load_context(
#             session['SESSION_NAME'], 
#             table_name='interim_collections'
#             )

#         # Perform the embedding process here
#         print('Embedding process started...')
#         pages_embed_df = cproc.embed_pages(pages_refined_df)
#         print('Embedding process finished.')
#         ## TODO: use vectorstore to store embeddings
#         print('!!!!!', pages_embed_df['embedding'].dtype)
#         pages_embed_df['embedding'] = pages_embed_df['embedding'].astype(str)

#         ## DMODEL UPDATE
#         ## Decouple context from embeddings
#         ## TODO: implement UUID for context
#         to_serialize_df = pages_embed_df[['session_name', 'embedding']]
#         embed_df = cproc.serialize_embedding(to_serialize_df)
#         print(embed_df.head())
#         #######################

#         # insert data with embedding to main context table with if exist = append.
#         db_conn.insert_context(pages_embed_df)

#     # Proceed to the chatbot
#     return redirect(url_for('index'))




def open_browser():
    """Open default browser to display the app in PROD mode
    """
    webbrowser.open_new('http://127.0.0.1:5000/')



if __name__ == '__main__':
    # Run DEV server
    app.run(debug=True, host='0.0.0.0', port=5000)

    # run PROD server
    # Timer(1, open_browser).start()
    # serve(app, host='0.0.0.0', port=5000)