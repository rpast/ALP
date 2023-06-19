"""Handles the database connection and queries.
"""

import os
import sqlite3
import tiktoken
import pandas as pd
# import params as prm
from oai_tool import get_embedding
from cont_proc import create_uuid


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

    def __enter__(self):
        """Enter the context manager."""
        self.create_connection()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        self.close_connection()


    

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
    def insert_session(self, uuid, col_uuid, sname, sdate) -> bool:
        """Insert session data into the database's Sessions table.
        :param sname: session name
        :param sdate: session date
        :return:
        """
        try:
            c = self.conn.cursor()
            
            c.execute(f"""
                INSERT INTO session 
                VALUES ('{uuid}', '{col_uuid}', '{sname}', '{sdate}')
                """)
            self.conn.commit()

            print(f"Session: \"{sname}\" inserted into the database")
            return True
        
        except Exception as e:
            print(e)



    def insert_context(self, context_df, table_name='collections', if_exist='append'):
        """Insert context data into the database
        :param context_df: context dataframe
        :return:
        """
        try:
            context_df.to_sql(
                table_name, 
                self.conn, 
                if_exists=if_exist, 
                index=False
                )
            print (f"Context data inserted into the {table_name} table")
            return True
        except Exception as e:
            print(e)
            return False

    def insert_embeddings(self, embedding_df, table_name='embeddings', if_exist='append'):
        """Insert embeddings data into the database
        :param embedding_df: embeddings dataframe
        :return:
        """
        try:
            embedding_df.to_sql(
                table_name, 
                self.conn, 
                if_exists=if_exist, 
                index=False
                )
            print (f"Embeddings inserted into the {table_name} table")
            return True
        except Exception as e:
            print(e)
            return False

    def insert_interaction(
            self, 
            session_uuid,
            inter_type, 
            message, 
            page=None,
            timestamp=0) -> bool:
        """Insert interaction data into the database's Interaction table.
        :param inter_type: interaction type
        :param message: interaction message
        :param page: page number
        :param timestamp: timestamp
        :return:
        """

        uuid = create_uuid()
        embedding = get_embedding(message)

        encoding = tiktoken.encoding_for_model('gpt-3.5-turbo')
        num_tokens_oai = len(encoding.encode(message))

        message = message.replace('"', '').replace("'", "")

        query = f"""
            INSERT INTO chat_history 
            VALUES (
                '{session_uuid}', 
                '{uuid}', 
                '{inter_type}', 
                '{message}', 
                '{num_tokens_oai}', 
                '{page}', 
                '{embedding}',
                '{timestamp}'
                )
            """

        try:
            c = self.conn.cursor()
            c.execute(
                query
                )

            self.conn.commit()

            print(f"Interaction type: \"{inter_type}\" inserted into the database for session: \"{session_uuid}\"")

            return True
        
        except Exception as e:
            print(e)

            return False


    def load_context(self, session_uuid, table_name='collections') -> pd.DataFrame:
        """Load context data from the database to a dataframe
        :param table_name: table name
        :return:
        """

        # if session_uuid is not a list, turn it into a list
        if not isinstance(session_uuid, list):
            session_uuid = [session_uuid]

        # Prepare placeholders for the query
        placeholders = ', '.join('?' for _ in session_uuid)

        try:
            c = self.conn.cursor()
            c.execute(
                f"SELECT * FROM {table_name} WHERE UUID in ({placeholders})",
                session_uuid
                )
            data = c.fetchall()
            # get column names
            # print([desc[0] for desc in c.description])
            colnames = [desc[0] for desc in c.description]
            context_df = pd.DataFrame(data, columns=colnames)
            context_df['timestamp'] = pd.to_numeric(context_df['timestamp'])
            return context_df

        except Exception as e:
            print(e)

            return None
        

    def load_collections(self, session_uuid) -> list:
        """Load collection ids associated with the given session id
        """
        try:
            c = self.conn.cursor()
            c.execute(f"SELECT DISTINCT collection_uuid FROM session WHERE UUID = '{session_uuid}'")
            data = c.fetchall()

            return [d[0] for d in data]
        
        except Exception as e:
            print(e)

            return None
        
    def load_collections_all(self) -> list:
        """Load all collection names and uuids available in db.collections
        """
        try:
            c = self.conn.cursor()
            c.execute(f"SELECT DISTINCT uuid, name FROM collections")
            data = c.fetchall()
            #if data is empty return []
            # if not data:
            #     return []
            return data

        except Exception as e:
            print(e)

            return None


    # method to load all session names from context table in the database
    def load_session_names(self, table_name='session') -> list:
        """Load session names and dates from the database to a list
        :param table_name: table name
        :return:
        """
        try:
            c = self.conn.cursor()
            c.execute(f"SELECT DISTINCT name, uuid, date FROM {table_name}")
            data = c.fetchall()
            return data
        
        except Exception as e:
            print(e)

            return None


    # method to delete a given session from the database
    def delete_session(self, session_name) -> bool:
        """Delete a session from the database
        :param session_name: session name
        :return:
        """
        try:
            c = self.conn.cursor()
            c.execute(f"DELETE FROM collections WHERE SESSION_NAME = '{session_name}'")
            self.conn.commit()
            print(f"Session: \"{session_name}\" deleted from the database")
            return True
        
        except Exception as e:
            print(e)

            return False


