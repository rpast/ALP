from flask import Flask, request, render_template, redirect, url_for, jsonify
#import your_module_name  # Replace 'your_module_name' with the name of the file containing your original code

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    question = request.form['question']
    session_name = request.form['session_name']
    response='DADA'
    # response = your_module_name.process_question(question, session_name)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)


