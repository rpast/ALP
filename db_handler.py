"""Handles the database connection and queries.
"""

import sqlite3
import tiktoken
import params as prm
from oai_tool import get_embedding

## DB utilities ##

# Generic DB functions
def create_connection(db_file):
    """ create a database connection to the SQLite database
    specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)

    return conn


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Exception as e:
        print(e)


def parse_tables(conn):
    """Parse the tables in the database
    :param conn: Connection object
    :return:
    """
    try:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return c.fetchall()
    except Exception as e:
        print(e)


def query_db(conn, query):
    """Query the database
    :param conn: Connection object
    :param query: SQL query
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(query)
        return c.fetchall()
    except Exception as e:
        print(e)


def write_db(conn, query):
    """Write to the database
    :param conn: Connection object
    :param query: SQL query
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(query)
        conn.commit()
    except Exception as e:
        print(e)


# App specific DB functions
def insert_session(conn, sname, sdate):
    """Insert session data into the database
    :param conn: Connection object
    :param sname: session name
    :param sid: session id
    :param sdate: session date
    :return:
    """
    try:
        c = conn.cursor()
        # if session name already in the session table, then don't insert and return info
        c.execute(f"SELECT * FROM session WHERE session_name = '{sname}'")
        if c.fetchall():
            print(f"Session: \"{sname}\" already in the database")
            return None
        
        if sname.find('-') == '-1':
            print("Session name cannot contain \"-\",\"!\",\"?\",\".\" characters")
            return None
        
        
        c.execute(f"INSERT INTO session VALUES ('{sname}', '{sdate}')")
        conn.commit()

        print(f"Session: \"{sname}\" inserted into the database")
        return True
    
    except Exception as e:
        print(e)


def insert_context(conn, session_name, context_df):
    """Insert context data into the database
    :param conn: Connection object
    :param session_name: session name
    :param context_df: context dataframe
    :return:
    """
    try:
        context_df.to_sql(f'context_{session_name}', conn, if_exists='replace', index=False)
        print (f"Context table for session: \"{session_name}\" created")
        return True
    except Exception as e:
        print(e)
        return False


def insert_interaction(conn, session_name, inter_type, message, timestamp=0):
    """Insert interaction data into the database
    :param conn: Connection object
    :param session_name: session name
    :param inter_type: interaction type (user, assistant)
    :param messages: list of messages
    :param embeddings: list of embeddings
    :return:
    """

    embedding = get_embedding(message)

    encoding = tiktoken.encoding_for_model('gpt-3.5-turbo-0301')
    num_tokens_oai = len(encoding.encode(message))

    message = message.replace('"', '').replace("'", "")

    try:
        c = conn.cursor()
        c.execute(f"INSERT INTO interaction_{session_name} VALUES ('{session_name}', '{inter_type}', '{message}', '{embedding}','{num_tokens_oai}', '{timestamp}')")
        conn.commit()
        print(f"Interaction type: \"{inter_type}\" inserted into the database for session: \"{session_name}\"")
        return True
    except Exception as e:
        print(e)
        return False
    

def bulk_insert_interaction(conn, usr_txt, asst_txt, session_name):
    """
    Insert user and assistant interactions into DB
    """
    # Open DB so the assistant can remember the conversation
    conn = create_connection(prm.DB_PTH)
    # Insert user message into DB so we can use it for another user's input
    insert_interaction(
        conn, 
        session_name, 
        'user', 
        usr_txt
        )
    # Insert model's response into DB so we can use it for another user's input
    insert_interaction(
        conn,
        session_name,
        'assistant',
        asst_txt
        )
    conn.close()
    