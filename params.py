"""This file contains all the parameters for the project
"""

from pathlib import Path


## General parameters ##
IN_PTH = Path('./input')
D_PTH = Path('./data')

TOKEN_THRES = 500 # Number of tokens to split the document into chunks
NUM_SAMPLES = 5 # Number of samples to take from the document


## SQL parameters ##
# Session name is defined by the user

## Create a table in the database where session data will be stored
DB_PTH = D_PTH / 'aleph.db'

# INTERACTION_TABLE_SQL = """ 
#     CREATE TABLE IF NOT EXISTS interaction (
#         session_name,
#         session_date, 
#         id, 
#         created, 
#         completion_tokens, 
#         prompt_tokens, 
#         total_tokens, 
#         role, 
#         message_text
#     ) 
#     """


CONTEXT_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS context (
        session_name,
        chapter_title,
        chapter_text,
        chapter_token_no,
        chapter_embeddings        
        )"""


SESSION_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS session (
        session_name,
        session_date
        )"""