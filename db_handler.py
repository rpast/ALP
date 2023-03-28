"""Handles the database connection and queries.
"""

import os
import sqlite3
import tiktoken
import pandas as pd
import params as prm
from oai_tool import get_embedding


class DatabaseHandler:
    """Handles the database connection and queries. One instance per database file.
    """

    
    def __init__(self, db_file):
        """Create a new database file if it doesn't exist, otherwise connect to the existing database file."""
        self.db_file = db_file
        if os.path.exists(db_file):
            print(f"Database file '{db_file}' already exists.")
            self.create_connection(db_file)
        else:
            print(f"Creating a new database file '{db_file}'.")
            self.create_connection(db_file)


    def create_connection(self, db_file=None):
        """Create a database connection to the SQLite database specified by db_file attribute."""
        if db_file is None:
            db_file = self.db_file
        elif db_file != self.db_file:
            print('Warning: db_file argument does not match the db_file attribute. Using the db_file attribute instead.')
            db_file = self.db_file
        
        self.conn = None
        try:
            self.conn = sqlite3.connect(db_file)
            print(f'Established connection to database \'{db_file}\'')
        except Exception as e:
            print(e)


    def close_connection(self):
        """Close the connection to the database.
        """
        if self.conn is not None:
            self.conn.close()
            print(f'Closed connection to database \'{self.db_file}\'.')
        else:
            print('No connection to close.')


    def parse_tables(self) -> list:
        """Parse the database and return a list of table names.
        :return: list of table names
        """
        try:
            c = self.conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table';")
            return c.fetchall()
        except Exception as e:
            print(e)


    def query_db(self, query) -> list:
        """Query the database.
        :param query: SQL query
        :return: list of tuples
        """
        try:
            c = self.conn.cursor()
            c.execute(query)
            return c.fetchall()
        except Exception as e:
            print(e)


    def write_db(self, query) -> None:
        """Write to the database.
        :param query: SQL query
        :return: None
        """
        try:
            c = self.conn.cursor()
            c.execute(query)
            self.conn.commit()
            print(f'Query: \'{query}\' executed')
        except Exception as e:
            print(e)


    # TODO: use high performance library for writing pandas dataframes to sqlite
    def insert_session(self, sname, sdate) -> bool:
        """Insert session data into the database's Sessions table.
        :param sname: session name
        :param sdate: session date
        :return:
        """
        try:
            c = self.conn.cursor()
            # if session name already in the session table, then don't insert and return info
            c.execute(f"SELECT * FROM session WHERE session_name = '{sname}'")
            if c.fetchall():
                print(f"Session: \"{sname}\" already in the database")
                return False
            
            # TODO: use dedicated python library for string validation
            if sname.find('-') == '-1':
                print("Session name cannot contain \"-\",\"!\",\"?\",\".\" characters")
                return False
            
            
            c.execute(f"INSERT INTO session VALUES ('{sname}', '{sdate}')")
            self.conn.commit()

            print(f"Session: \"{sname}\" inserted into the database")
            return True
        
        except Exception as e:
            print(e)


    def insert_context(self, context_df, table_name='context', if_exist='append'):
        """Insert context data into the database
        :param context_df: context dataframe
        :return:
        """
        try:
            context_df.to_sql(table_name, self.conn, if_exists=if_exist, index=False)
            print (f"Context data inserted into the {table_name} table")
            return True
        except Exception as e:
            print(e)
            return False
        

    def load_context(self, session_name, table_name='context') -> pd.DataFrame:
        """Load context data from the database to a dataframe
        :param table_name: table name
        :return:
        """
        try:
            c = self.conn.cursor()
            c.execute(f"SELECT * FROM {table_name} WHERE SESSION_NAME = '{session_name}'")
            data = c.fetchall()
            # get column names
            colnames = [desc[0] for desc in c.description]
            context_df = pd.DataFrame(data, columns=colnames)

            return context_df
        
        except Exception as e:
            print(e)

            return None


    def insert_interaction(self, session_name, inter_type, message, page=None, edges=None, timestamp=0) -> bool:
        """Insert interaction data into the database's Interaction table.
        :param session_name: session name
        :param inter_type: interaction type
        :param message: interaction message
        :param page: page number
        :param edges: edges
        :param timestamp: timestamp
        :return:
        """

        embedding = get_embedding(message)

        encoding = tiktoken.encoding_for_model('gpt-3.5-turbo')
        num_tokens_oai = len(encoding.encode(message))

        message = message.replace('"', '').replace("'", "")

        query = f"INSERT INTO context VALUES ('{session_name}', '{inter_type}', '{message}', '{num_tokens_oai}', '{page}', '{embedding}', '{edges}','{timestamp}')"

        try:
            c = self.conn.cursor()
            c.execute(
                query
                )

            self.conn.commit()

            print(f"Interaction type: \"{inter_type}\" inserted into the database for session: \"{session_name}\"")

            return True
        
        except Exception as e:
            print(e)

            return False


    def fetch_recall_table(self, session_name) -> pd.DataFrame:
        """Query the database for the recall table for the given session_name
        Recal table is a table that contains the context data for the given session_name and the interaction data for the given session_name

        :param session_name: session name
        :return: recal table pd.DataFrame
        """
        # Define the query to fetch the context table for the given session_name
        select_context = f"SELECT * FROM context_{session_name}"
        
        # Define the query to check if interaction table for given session_name exists in the database
        check_interaction = f"SELECT name FROM sqlite_master WHERE type='table' AND name='interaction_{session_name}'"

        # Fetch context table for given session_name
        context_df = pd.read_sql_query(select_context, self.conn)
        
        # Check if interaction table for given session_name exists in the database
        inter_check = query_db(self.conn, check_interaction)
        if not inter_check:
            print(f"Interaction table for session: \"{session_name}\" does not exist in the database. Fetcging context table only.")
            interaction_df = pd.DataFrame(columns=['session_name', 'interaction_type', 'messages', 'embeddings'])
        else:
            interaction_df = pd.read_sql_query(f"SELECT * FROM interaction_{session_name}", self.conn)
        
        # Create one master dataframe with context and interaction data
        master_df = pd.concat([context_df, interaction_df], ignore_index=True)

        return master_df
    

    def __repr__(self) -> str:
        return f"DBManager({self.db_file})"




## DB functions utilities ##

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


def fetch_recall_table(session_name, conn):
    """Query the database for the recall table for the given session_name
    Recal table is a table that contains the context data for the given session_name and the interaction data for the given session_name

    :param session_name: session name
    :return: recal table pd.DataFrame
    """

    select_context = f"SELECT * FROM context_{session_name}"
    check_interaction = f"SELECT name FROM sqlite_master WHERE type='table' AND name='interaction_{session_name}'"


    # Fetch context table for given session_name
    context_df = pd.read_sql_query(select_context, conn)
    interaction_df = pd.DataFrame(columns=['session_name', 'interaction_type', 'messages', 'embeddings'])

    # Check if interaction table for given session_name exists in the database
    inter_check = query_db(conn, check_interaction)
    if not inter_check:
        print(f"Interaction table for session: \"{session_name}\" does not exist in the database.")
    else:
        interaction_df = pd.read_sql_query(f"SELECT * FROM interaction_{session_name}", conn)
    
    # Create one master dataframe with context and interaction data
    master_df = pd.concat([context_df, interaction_df], ignore_index=True)

    return master_df
    