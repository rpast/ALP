"""This file contains all the parameters for the project
"""

import os, sys
from pathlib import Path


## General parameters ##
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DB_FOLDER = os.path.join(STATIC_FOLDER, "data", "dbs")
UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, "data", "uploads")

DB_FOLDER = Path(f'./static/data/dbs')
UPLOAD_FOLDER = Path(f'./static/data/uploads')

DB_NAME = 'app.db'
DB_PATH = os.path.join(DB_FOLDER, DB_NAME)

CNT_TABLE_NAME = 'context'
CNT_INTERIM_TABLE_NAME = 'interim_context'
SESSION_TABLE_NAME = 'session'


TOKEN_THRES = 500 # Number of tokens to split the document into chunks
NUM_SAMPLES = 5 # Number of samples to take from the document


# Model context management
SUMMARY_CTXT_USR = "How would you act when I'd ask you what this document is about. Can you summarize it for me?"
SUMMARY_TXT_ASST = "When a user asks me to summarize the source material or explain what it is about, I would look for the best text fragment that provides general information about the document's contents. To find a text fragment for summarization, I suggest starting by scanning the abstract and conclusion sections, and also checking the table of contents."


## SQL parameters ##
# Session name is defined by the user

# TODO: session_source not needed
SESSION_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS session (
    
        uuid TEXT NOT NULL,
        collection_uuid TEXT NOT NULL,
    
        name TEXT NOT NULL,
        date TEXT NOT NULL
        )"""

# INTERIM_COLLECTIONS_TABLE_SQL = """
#     CREATE TABLE IF NOT EXISTS interim_collections (
    
#         uuid TEXT NOT NULL,
#         doc_uuid TEXT NOT NULL,
    
#         session_name TEXT NOT NULL,
#         interaction_type TEXT NOT NULL,
#         text TEXT NOT NULL,
#         text_token_no INTEGER,
#         page INTEGER
#         )"""

COLLECTIONS_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS collections (
        
        uuid TEXT NOT NULL,
        doc_uuid TEXT NOT NULL,

        name TEXT NOT NULL,
        interaction_type TEXT NOT NULL,
        text TEXT NOT NULL,
        text_token_no INTEGER,
        page INTEGER,
        embedding TEXT NOT NULL,
        timestamp INTEGER
        )"""

# This doesnt need a session_name
CHAT_HIST_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS chat_history (
    
        uuid TEXT NOT NULL,
        doc_uuid TEXT NOT NULL,

        interaction_type TEXT NOT NULL,
        text TEXT NOT NULL,
        text_token_no INTEGER,
        page INTEGER,
        embedding BLOB NOT NULL,
        timestamp INTEGER
        )"""

# uuid is a FK -> context table, chat_history table
EMBEDDINGS_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS embeddings (
        uuid TEXT NOT NULL,
        embedding BLOB NOT NULL
        )"""