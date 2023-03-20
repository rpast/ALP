import openai, os

import pandas as pd
import logic_bak.utils as utl
import params as prm

from tqdm import tqdm
from datetime import date, datetime


api_key = os.environ['OAI_KEY']
openai.api_key = api_key


# Grab current local date
today = date.today()

process_doc = input('Do you want to process the document? (y/n): ')
session_name = input('Enter session name: ')
session_date = today



# Connect to user's database ##################################################
print('Creating database for the session...')

conn = utl.create_connection(prm.DB_PTH) # Create connection to the database

utl.create_table(conn, prm.SESSION_TABLE_SQL) # Create table if it does not exist
# Create interaction table for the session
utl.create_table(conn, f"CREATE TABLE IF NOT EXISTS interaction_{session_name} (session_name, interaction_type, text, embedding, num_tokens_oai, time_signature)")

tables = utl.parse_tables(conn) # Grab tables to check if the table was created

# DB INTERACTION
# Write session data to the database
utl.insert_session(conn, session_name, session_date) # Insert session data  

conn.close()
###############################################################################



pages_contents_long_df = pd.read_csv(prm.D_PTH  / f'{session_name}_embeded.csv')

# DB error fix:
# chapter_contents_long_df['embedding'] = chapter_contents_long_df['embedding'].apply(json.dumps)
pages_contents_long_df['embedding'] = pages_contents_long_df['embedding'].astype(str)

# DB INTERACTION
# Insert context into DB
conn = utl.create_connection(prm.DB_PTH)
utl.insert_context(conn, session_name, pages_contents_long_df)
conn.close()

# Buiild seed conversation context for summarization
# TODO: no need to get embedding each time the script is run. Optimize it.
# TODO: put this to params.py



utl.bulk_insert_interaction(
    conn, 
    prm.SUMMARY_CTXT_USR, 
    prm.SUMMARY_TXT_ASST, 
    session_name
    )


while True:
    # POC - conversational interface

    ## Get unix time
    query_time = int(datetime.now().timestamp())
    ## User input
    print('User input')
    question = input(">>> ")
    # question = prmt

    if question == 'exit':
        break
    

    ## Fetch recal table so we can compare user input to embeddings saved in it and fetch the right context.
    recal_table = utl.fetch_recall_table(session_name)

    ## Chop recall table to only include contexts for sources, user, or assistant
    recal_table_source = recal_table[recal_table['interaction_type'] == 'source']
    recal_table_user = recal_table[recal_table['interaction_type'] == 'user']
    recal_table_assistant = recal_table[recal_table['interaction_type'] == 'assistant']

    recal_embed_source = utl.convert_table_to_dct(recal_table_source)
    recal_embed_user = utl.convert_table_to_dct(recal_table_user)
    recal_embed_assistant = utl.convert_table_to_dct(recal_table_assistant)

    ## Get the context from recal table that is the most similar to user input
    if recal_table_source.shape[0]<prm.NUM_SAMPLES:
        num_samples = recal_table_source.shape[0]
        print('Source material is shorter than number of samples you want to get. Setting number of samples to the number of source material sections.')

    ## Get SRC context
    if len(recal_embed_source) == 0:
        recal_source = 'No context found'
    else:
        recal_source_id = utl.order_document_sections_by_query_similarity(question, recal_embed_source)[0:prm.NUM_SAMPLES]
        # If recal source id is a list, join the text from the list
        if len(recal_source_id)>1:
            idxs = [x[1] for x in recal_source_id]
            recal_source = recal_table.loc[idxs]['text'].to_list()
            recal_source = '| '.join(recal_source)
        else: 
            recal_source = recal_table.loc[recal_source_id[1]]['text']
    ## GET QRY context
    if len(recal_embed_user) == 0:
        recal_user = 'No context found'
    else:
        recal_user_id = utl.order_document_sections_by_query_similarity(question, recal_embed_user)[0][1]
        recal_user = recal_table.loc[recal_user_id]['text']
    ## GET RPL context
    if len(recal_embed_assistant) == 0:
        recal_assistant = 'No context found'
    else:
        recal_assistant_id = utl.order_document_sections_by_query_similarity(question, recal_embed_assistant)[0][1]
        recal_assistant = recal_table.loc[recal_assistant_id]['text']


    # Look for assistant and user messages in the interaction table that have the latest time_signature
    last_usr_max = recal_table_user['time_signature'].astype(int).max()
    last_asst_max = recal_table_assistant['time_signature'].astype(int).max()
    if last_usr_max == 0:
        latest_user = 'No context found'
    else:
        latest_user = recal_table_user.loc[recal_table_user['time_signature']==str(last_usr_max)]['text'].values[0]

    if last_asst_max == 0:
        latest_assistant = 'No context found'
    else:
        latest_assistant = recal_table_assistant.loc[recal_table_assistant['time_signature']==str(last_asst_max)]['text'].values[0]


    ## Grab chapter name if it exists, otherwise use session name
    ## It will become handy when user wants to know from which chapter the context was taken
    if len(idxs)>1:
        recal_source_pages = recal_table.loc[idxs]['page'].to_list()
    else:
        recal_source_pages = recal_table.loc[recal_source_id[1]]['page']

    print(f'I will answer your question basing on the following context: {set(recal_source_pages)}')

    ###############################################################################
    # Set-up system prompts. This is done once for the whole session and the setup depends on the type of assistant chosen by the user.
    # I comnment this out as this needs to be saved in the interaction table and I will implement this after user-assistant interactions are implemented.

    sys_message = {
            'role': 'system', 
            'content': "You are a helpful assistant. You provide only factual information. If you do not know the answer, you say it. I provide my input after INP tag. I will pass the context you will use in your answer. I encode it with following tags: SRC - sources we are talking about; QRY - one of previous inputs I passed to you in the conversation; RPL - one of your previous replies to my questions from the conversation."
            }
    prev_user = {"role": "user", "content": f"{latest_user}"}
    prev_assistant = {"role": "assistant", "content": f"{latest_assistant}"}
    user_message = {
            "role": "user", 
            "content": f"SRC: {recal_source}. QRY: {recal_user}. RPL: {recal_assistant}. INP: {question}"
            }

    ###############################################################################

    ## Form user message based on recaled context and user's input
    usr_message = [
        sys_message,
        prev_user,
        prev_assistant,
        user_message
        ]

    # Count number of tokens in user message and display it to the user
    token_passed = utl.num_tokens_from_messages(usr_message)
    context_capacity =  4096 - token_passed
    print(f"Number of tokens passed to the model: {token_passed}")
    print(f"Number of tokens left in the context: {context_capacity}")

    # Grab call user content from messages alias
    usr_message_content = usr_message[0]['content']


    ## Make API call with formed user message
    api_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=usr_message
    )


    # Open DB so the assistant can remember the conversation
    conn = utl.create_connection(prm.DB_PTH)
    # Insert user message into DB so we can use it for another user's input
    utl.insert_interaction(
        conn, 
        session_name, 
        'user', 
        question,
        query_time
        )
    # Insert model's response into DB so we can use it for another user's input
    utl.insert_interaction(
        conn,
        session_name,
        'assistant',
        api_response['choices'][0]['message']['content'],
        api_response['created']
        )
    conn.close()


    ## Print CALL and RESPONSE
    print('USER:')
    print(question)
    print('\n')
    print('ASSISTANT:')
    print(api_response['choices'][0]['message']['content'])
    print('\n')
    print('-------------')
    print('\n')
