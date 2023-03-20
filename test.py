import sqlite3 from flask import Flask, request 

app = Flask(__name__) 

# Define a function to create a new database connection for each user 

def get_db(user_id): 
    db_name = 'user_{}_db.sqlite'.format(user_id) 
    db = sqlite3.connect(db_name) 
    return db

# Define a Flask route for user login 
# 
@app.route('/login') 
def login(): 
    user_id = request.args.get('user_id') 
    # or however you get the user's unique identifier 
    db = get_db(user_id) 
    # do whatever you need to authenticate the user 
    # ... 
    return 'Welcome, {}'.format(user_id) 

# Define a Flask route for accessing user data 

@app.route('/data') 
def data(): 
    user_id = request.args.get('user_id') 
    db = get_db(user_id) 
    # do whatever you need to retrieve and display the user's data 
    # # ... 
    return 'Data for user {}'.format(user_id) 

if __name__ == '__main__': app.run(debug=True)