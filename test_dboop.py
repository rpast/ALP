import params as pm
import cont_proc as cproc
from db_handler import DatabaseHandler

import openai
import numpy as np
from langchain.document_loaders import PyPDFLoader

openai.api_key = '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'

# create db
db = DatabaseHandler('app.db')
# create session, interim context and context tables
db.write_db(pm.SESSION_TABLE_SQL)
db.write_db(pm.INTERIM_CONTEXT_TABLE_SQL)
db.write_db(pm.CONTEXT_TABLE_SQL)
# insert session name
db.insert_session('test_session_autom', '2023-03-28')

# load pdf
loader = PyPDFLoader('./static/data/uploads/smgt1_1679946376_retrieval_augmentation.pdf')
pages = loader.load_and_split()
test_df = cproc.pages_to_dataframe(pages)
test_split_df = cproc.split_pages(test_df, 'test_session_autom')

# insert test_split_df data to interim context
db.insert_context(test_split_df, table_name='interim_context', if_exist='replace')

# load data from interim context to df
df = db.load_context('test_session_autom', table_name='interim_context')

# embed pages
pages_embed_df = cproc.embed_pages(df)

# Insert pages_embed_df to context
# turn embedding data to str
pages_embed_df['embedding'] = pages_embed_df['embedding'].astype(str)
pages_embed_df['edges'] = np.nan

db.insert_context(pages_embed_df)

#insert baseline interaction
db.insert_interaction(
    'test_session_autom', 
    'user',
    pm.SUMMARY_CTXT_USR
)
db.insert_interaction(
    'test_session_autom', 
    'assistant',
    pm.SUMMARY_TXT_ASST
)