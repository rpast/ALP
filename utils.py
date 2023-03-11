import numpy as np
import sqlite3
import tiktoken
import openai
import ast
from sqlite3 import Error
import params as prm # import parameters from params.py


## DB utilities ##

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
    except Error as e:
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
    except Error as e:
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
    except Error as e:
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
    except Error as e:
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
    except Error as e:
        print(e)


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
        elif sname.find('-'):
            print("Session name cannot contain \"-\",\"!\",\"?\",\".\" characters")
            return None
        else:
            c.execute(f"INSERT INTO session VALUES ('{sname}', '{sid}', '{sdate}')")
            conn.commit()
    except Error as e:
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
    except Error as e:
        print(e)
        return False


## Processing utilities ##

def split_contents(x):
    """Split contents into number of chunks defined by split_factor
    if split factor = 2 then split contents into 2 chunks
    """
    thres = int(len(x['contents'])/x['split_factor'])

    return [x['contents'][i:i+thres] for i in range(0, len(x['contents']), thres)]
    
    # textlen = len(contents)
    # splitlen = int(textlen/split_factor)
    # if splitlen > 0:
    #     return [contents[i:i+splitlen] for i in range(0, textlen, splitlen)]
    # else:
    #     return [contents]


## OAI utilities ##

# Count tokens for each chapter
def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages.
    """
    
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")


# Build simple embedding function
def get_embedding(text, model="text-embedding-ada-002"):
    """Returns the embedding for a given text.
    """
    return openai.Embedding.create(
        input=text, 
        model=model,
        )['data'][0]['embedding']


def vector_similarity(x, y):
    """
    Returns the similarity between two vectors.
    
    Because OpenAI Embeddings are normalized to length 1, the cosine similarity is the same as the dot product.
    """

    # Catch all ys that are not lists or arrays
    if not isinstance(y, (list, np.ndarray)):
        return 0

    x = np.array(x, dtype=np.float32)
    y = np.array(y, dtype=np.float32)


    if len(x) < len(y):
        # pad x with zeros to match the length of y
        x = np.concatenate([x, np.zeros(y.shape[0] - x.shape[0], dtype=np.float32)])
    elif len(y) < len(x):
        # pad y with zeros to match the length of x
        y = np.concatenate([y, np.zeros(x.shape[0] - y.shape[0], dtype=np.float32)])

    # Make sure I return single scalar value


    return np.dot(x,y)


def order_document_sections_by_query_similarity(query, contexts):
    """
    Find the query embedding for the supplied query, and compare it against all of the pre-calculated document embeddings
    to find the most relevant sections. 
    
    Return the list of document sections, sorted by relevance in descending order.
    """
    query_embedding = get_embedding(query)
    
    document_similarities = sorted(
        [
            (vector_similarity(query_embedding, ast.literal_eval(doc_embedding)), doc_index) for doc_index, doc_embedding in contexts.items()
            ], reverse=True
        )
    
    return document_similarities