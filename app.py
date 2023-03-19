import os, openai
from flask import Flask, request, render_template, redirect, url_for, jsonify
from chatbot import Chatbot
#import your_module_name  # Replace 'your_module_name' with the name of the file containing your original code

app = Flask(__name__)


# initialize classes
chatbot = Chatbot()
print("Chatbot initialized")


# Render welcome page
@app.route('/')
def welcome():
    return render_template('welcome.html')


@app.route('/set_api_key', methods=['POST'])
def set_api_key():
    """Set the API key as an environment variable."""
    api_key = request.form['api_key']
    openai.api_key = api_key
    return redirect(url_for('session_start'))

#################
# DOING: user uploads pdf and sets session name. 
# Then, the pdf is uploaded to the server, processed, 
# contents saved in SQLite database, session name saved as
# environ variable
@app.route('/session')
def session_start():
    """Render session start page"""
    return render_template('session_start.html')

## IN PROGRESS... =>
@app.route('/set_session', methods=['POST'])
def set_session():
    """Set the session name and upload doc."""
    data = request.get_json()
    session_name = data['session_name']
    file = data['file']
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


