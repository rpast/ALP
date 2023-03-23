"""This file contains all the parameters for the project
"""

from pathlib import Path


## General parameters ##
DB_FOLDER = Path('./data/dbs')
UPLOAD_FOLDER = Path('./data/uploads')

TOKEN_THRES = 500 # Number of tokens to split the document into chunks
NUM_SAMPLES = 5 # Number of samples to take from the document


# Model context management
SUMMARY_CTXT_USR = "How would you act when I'd ask you what this document is about. Can you summarize it for me?"
SUMMARY_TXT_ASST = "When a user asks me to summarize the source material or explain what it is about, I would look for the best text fragment that provides general information about the document's contents. To find a text fragment for summarization, I suggest starting by scanning the abstract and conclusion sections, and also checking the table of contents."


## SQL parameters ##
# Session name is defined by the user

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