import os, openai, time, datetime


from flask import Flask, request, render_template, redirect, url_for, jsonify
from langchain.document_loaders import PyPDFLoader

from chatbot import Chatbot
import params as prm
import doc_proc as dproc
import db_handler as dbh



app = Flask(__name__)
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
    session = request.form['session_name']
    file = request.files['pdf']

    # Create the db and file codes + save the file
    app.config['DB_CODE'] = session + '_' + app.config['TIME']

    file_name = app.config['DB_CODE'] + '_' + file.filename.lower().strip().replace(' ', '_')
    fpath = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    file.save(fpath)

    # Load the pdf and split it into pages
    loader = PyPDFLoader(fpath)
    pages = loader.load_and_split()

    # Process the pages and save to dbx
    pages_df = dproc.pages_to_dataframe(pages)
    pages_refined_df = dproc.split_pages(pages_df, app.config['DB_CODE'])
    
    # Create session and context table
    conn = dbh.create_connection(f"{app.config['DB_CODE']}.db")
    dbh.create_table(conn, prm.SESSION_TABLE_SQL)
    dbh.insert_session(conn, app.config['DB_CODE'], app.config['DATE'])
    dbh.insert_context(conn, app.config['DB_CODE'], pages_refined_df)
    conn.close()

    app.secret_key = api_key
    openai.api_key = app.secret_key

    return redirect(url_for('index'))

##################


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


