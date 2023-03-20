# TODO: figure out how session name should be passed here
import openai

import pandas as pd
import logic_bak.utils as utl
import params as prm

from tqdm import tqdm
from datetime import date


openai.api_key = prm.OAI_KEY
process_doc = False


# Document processing #########################################################
if process_doc:
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