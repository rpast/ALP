"""This file contains all the parameters for the project
"""

from pathlib import Path


## General parameters ##
IN_PTH = Path('./input')
D_PTH = Path('./data')
TITLE = 'biological-cognition.pdf'
IN_DOC_PTH = IN_PTH / TITLE


## SQL parameters ##
# Session name is defined by the user
# Session id is defined by the current time in UNIX timestamp

## Create a table in the database where session data will be stored
DB_PTH = D_PTH / 'tsun.db'

SESSION_TABLE_SQL = """ 
    CREATE TABLE IF NOT EXISTS session (
        session_name,
        session_id, 
        session_date, 
        id, 
        created, 
        completion_tokens, 
        prompt_tokens, 
        total_tokens, 
        role, 
        message_text
    ) 
    """

CONTEXT_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS context (
        session_id,
        chapter_title,
        chapter_text,
        chapter_token_no,
        chapter_embeddings        
        )"""