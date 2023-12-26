"""Contains static parameters for the project
"""

import os
from pathlib import Path


## General parameters ##
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

STATIC_FOLDER = Path('./static')
DB_FOLDER = Path(f'./static/data/dbs')
UPLOAD_FOLDER = Path(f'./static/data/uploads')

DB_NAME = 'app.db'
DB_PATH = os.path.join(DB_FOLDER, DB_NAME)

CNT_TABLE_NAME = 'context'
SESSION_TABLE_NAME = 'session'


TOKEN_THRES = 500 # Number of tokens to split the document into chunks
NUM_SAMPLES = 5 # Number of samples to take from the document

# List of available models
OPENAI_MODEL = ('gpt-3.5-turbo', 4096)
OPENAI_MODEL_16K = ('gpt-3.5-turbo-16k', 16384)
OPENAI_MODEL_V4 = ('gpt-4', 8192)
OPENAI_MODEL_V4_32K = ('gpt-4-32k', 32768)
OPENAI_MODEL_V4_1106 = ('gpt-4-1106-preview', 128000)

OPENAI_MODEL_EMBEDDING = 'text-embedding-ada-002'
SENTENCE_TRANSFORMER_MODEL = 'multi-qa-MiniLM-L6-cos-v1'

# prod model << Set this param to change the model used in production
PROD_MODEL = OPENAI_MODEL_V4_1106

# Set path to agent system messages
AGENT_INFO_PTH = Path(STATIC_FOLDER) / 'data' / 'simulacra.json'

# Model context management
SUMMARY_CTXT_USR = """
    How would you act when I'd ask you what's this document about or ask you to summarize source text?
    """
SUMMARY_TXT_ASST = """
    When a user asks me to summarize the source material or explain what it is about, 
    I would look for the best text fragment that provides general information about the document's contents. 
    To find a text fragment for summarization, I would start with the abstract and conclusion sections, 
    and also I'd check the table of contents.
    """


## DB parameters ##
# used when new db initialized under static/data/dbs/

SESSION_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS session (
    
        uuid TEXT NOT NULL,
        collection_uuid TEXT NOT NULL,
    
        name TEXT NOT NULL,
        date TEXT NOT NULL
        )"""

EMBEDDINGS_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS embeddings (
    
        uuid TEXT NOT NULL,
        embedding BLOB NOT NULL
        )"""

COLLECTIONS_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS collections (
        
        uuid TEXT NOT NULL,
        doc_uuid TEXT NOT NULL,

        name TEXT NOT NULL,
        interaction_type TEXT NOT NULL,
        text TEXT NOT NULL,
        text_token_no INTEGER,
        page INTEGER,
        timestamp INTEGER,
        embedding_model TEXT NOT NULL
        )"""

CHAT_HIST_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS chat_history (
    
        uuid TEXT NOT NULL,
        doc_uuid TEXT NOT NULL,

        interaction_type TEXT NOT NULL,
        text TEXT NOT NULL,
        text_token_no INTEGER,
        page INTEGER,
        timestamp INTEGER
        )"""