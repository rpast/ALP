import os, openai, time, datetime, json
import pandas as pd

from flask import Flask, request, session, render_template, redirect, url_for, jsonify

from langchain.document_loaders import PyPDFLoader

from chatbot import Chatbot
import params as prm
import cont_proc as cproc
import db_handler as dbh



app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = prm.UPLOAD_FOLDER

now = time.time()
date = datetime.datetime.fromtimestamp(now)
app.config['TIME'] = str(int(now))
app.config['DATE'] = date

# initialize classes
chatbot = Chatbot()
print("!Chatbot initialized")


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




###############################################################################

@app.route('/interaction')
def index():
    """render interaction main page"""
    return render_template('index.html')


@app.route('/ask', methods=['POST'])
def ask():
    """handle POST request from the form and return the response"""
    data = request.get_json()
    question = data['question']

    response = chatbot.chat_completion_response(question)
    return jsonify({'response': response})



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)