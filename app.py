import pandas as pd
import numpy as np
import openai, pickle, tiktoken, ast

from pathlib import Path
from tqdm import tqdm

import re, sqlite3

from pdfminer.high_level import extract_text

from collections import defaultdict

from datetime import date, datetime

import pprint

import utils as utl
import params as prm

import json

# Use your own key
# read secret key from the file 
with open('secret.txt', 'r') as f:
    openai.api_key = f.read()

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


# Document processing #########################################################
if process_doc.lower() == 'y':
    # print('Processing input document...')
    # # Currently we chop the document into chapters and then into smaller chunks
    # # TODO: User should decide if they want to chop the document into chapters or by page
    # #
    # # Logic for chapter capture
    # digit_word_rgx = r'^\d+(\.\d+)*\s[a-zA-Z]+.*$|Abstract'

    # # Load context document and grab chapter names
    # doc_name = input('Enter document name from input: ')

    # pdf_text = extract_text(prm.IN_PTH / doc_name)

    # chapters = utl.grab_chapters(pdf_text, matching_logic=2)

    # print('Script managed to capture the following chapters:')
    # for chapter in chapters:
    #     print(chapter)

    # # TODO: interface for selecting chapters to be used for text fragmentation. 
    # chapters = input('Enter chapters to be used for text fragmentation (separated by comma): ')
    # chapters = chapters.split(',')
    # chapters = [x.lower().strip() for x in chapters]
    # print(f"There are {len(chapters)} chapters in the document")

    # # Set a specific starting point of the document
    # # start = 'abstract'
    # start = input('Enter the starting point of the document: ')
    # start = start.lower().strip()

    # # TODO: make this text pre-processing function
    # # define the text to be parsed
    # text = [] 
    # for line in pdf_text.split('\n'):
    #     line = line.replace('\t', ' ')
    #     line = line.strip().lower()
    #     text.append(line)

    # text = ' '.join(text)
    # # replace newline and tab characters with space
    # text = text.replace('\n', '')
    # text = text.replace('\t', '')
    # text = re.sub(r'\s+', ' ', text)


    # # TODO: turn it into a function that will get triggered whe user decides to chop the document by chapter names

    # # Fragment the text according to the logic the user defined (currently - by chapters)

    # # join the end strings with | to form chapter end regex pattern
    # end_pattern = "|".join(chapters)

    # # match text between chapter and any end string
    # chapters_contents = {}
    # for string in chapters:

    #     pattern = rf"{string}(.*?)(" + end_pattern + "|$)"
    #     pattern = re.compile(pattern)



    #     # search for the pattern in the text
    #     match = pattern.search(text)

    #     # if there is a match, extract the text between string and any end-string
    #     if match:
    #         # get the first group of the match object, which is the text between given chapter and any end string
    #         result = match.group(1)

    #         # print or save or do whatever you want with the result
    #         chapters_contents[string] = result


    # #TODO: come up with test that checks if I grabbed all the chapters
    # fetched_chapters = [x for x in chapters_contents.keys()] 
    # # compare element wise fetched_chapters with chapters
    # missing_chapters = [x for x in chapters if x not in fetched_chapters]
    # print(f"Missing chapters: {missing_chapters}")

    # # Manually inspect some chapters
    # print('Printing the last 50 characters of the last chapter ', chapters_contents[chapters[-1]][-50:])
    

    doc_contents = utl.load_pdf()

    # Grab contents into a dataframe
    doc_contents_df = pd.DataFrame(doc_contents).T

    # Create a token count column
    doc_contents_df['num_tokens_oai'] = doc_contents_df['contents'].apply(
        lambda x: utl.num_tokens_from_messages([{'message': x}])
    )

    # For instances with token count > token_thres, split them so they fit model threshold so we could get their embeddings
    # TODO: make it split actually by tokens, not by characters

    # Calculate split factor for each chapter
    doc_contents_df['split_factor'] = 1
    doc_contents_df.loc[doc_contents_df['num_tokens_oai']>prm.TOKEN_THRES, 'split_factor'] = round(doc_contents_df['num_tokens_oai']/prm.TOKEN_THRES, 0)

    # Split contents
    doc_contents_df['contents_split'] = doc_contents_df.apply(
        lambda x: utl.split_contents(x), axis=1
        )

    # Explode the split contents
    pages_contents_long_df = doc_contents_df.explode(
        column='contents_split'
    )[['contents_split']]

    # Create a token count column (Again - this time for long table)
    pages_contents_long_df['num_tokens_oai'] = pages_contents_long_df['contents_split'].apply(
        lambda x: utl.num_tokens_from_messages([{'message': x}])
    )

    # Form text column for each fragment
    pages_contents_long_df['text'] = "PAGE: " + pages_contents_long_df.index.astype(str) + " CONTENT: " + pages_contents_long_df['contents_split']


    # Further dataframe processing
    pages_contents_long_df = (
        pages_contents_long_df
        .drop(columns=['contents_split']) # Drop contents_split column
        .reset_index() # Reset index so chapter names are stored in columns
        .rename(columns={'index': 'page'}) # Rename index column to chapter
        .assign(session_name=session_name) # Add session_name column
        .assign(interaction_type='source') ## Add interaction type column
        )
    ## Drop rows where num_tokens_oai is less than 25
    pages_contents_long_df = pages_contents_long_df[pages_contents_long_df['num_tokens_oai'] > 25].copy()


    ## GET EMBEDDINGS #############################################################
    contents_for_embed_df = pages_contents_long_df[['text']]
    # Calculate the cost of running the model to get embeddings
    embed_cost = (pages_contents_long_df['num_tokens_oai'].sum() / 1000) * 0.0004
    input(f"Embedding cost is {embed_cost}$. Press enter to continue")


    # Embed each chapter
    rng = tqdm(range(0,len(contents_for_embed_df)))

    contents_embedded = {}

    for i in rng:
        txt_page = contents_for_embed_df.index[i]
        txt_list = contents_for_embed_df.iloc[i].to_list()

        txt_embed = utl.get_embedding(txt_list)



        # Join embeddings with context table
        contents_embedded[txt_page] = txt_embed
    embeded_s = pd.Series(contents_embedded, index=contents_embedded.keys())

    # Merge embeddings with chapter contents
    pages_contents_long_df['embedding'] = embeded_s
    pages_contents_long_df.head()

    # Save embeddings
    pages_contents_long_df.to_csv(
        f'./data/{session_name}_embeded.csv',
        index=False
        )
    ###########################################################################

else:
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
