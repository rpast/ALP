import re 
import ast
import uuid
import pickle
import pandas as pd

import params as prm
from oai_tool import num_tokens_from_messages, get_embedding


## Various processors
def process_name(name):
    """Process name string to make it suitable for db and further processing.
    Current support for pdfs. In the future will support other file types.
    """

    # catch pdfs
    pdf_ = False
    if '.pdf' in name:
        # get name stem
        pdf_ = True
        name = name.split('.pdf')[0]

    name = name.strip()
    # exclude all signs that conflict with SQLite
    name = re.sub(r'[^\w]', '_', name)
    name = name.lower()

    # truncate if needed
    if len(name) > 100:
        name = name[:100]
    
    if pdf_:
        return name + '.pdf'
    else:
        return name


## Text processing functions
def clean_text(text):
    text = text.replace('\t', ' ')
    text = text.strip().lower()
    text = text.replace('\n', '')
    text = text.replace('\t', '')
    text = re.sub(r'\s+', ' ', text)
    return text


def long_date_to_short(date):
    """Convert long date to short date"""
    date = date.split(' ')[0]
    return date


def create_uuid():
    return str(uuid.uuid4())


def pages_to_dict(pages):
    """convert langchain.docstore.document.Document to dict"""
    pages_dict = {}
    for page in pages:
        pg_txt = page.page_content
        pg_txt = clean_text(pg_txt)
        pages_dict[page.metadata['page']] = pg_txt
    return pages_dict


def pages_to_dataframe(pages):
    """Convert dictionary of pages to dataframe"""
    pages_dct = pages_to_dict(pages)
    # # Grab contents into a dataframe
    doc_contents_df = pd.DataFrame(pages_dct, index=['contents']).T

    # # Create a token count column
    doc_contents_df['num_tokens_oai'] = doc_contents_df['contents'].apply(
        lambda x: num_tokens_from_messages([{'message': x}])
    )

    doc_contents_df = doc_contents_df.reset_index().rename(columns={'index': 'page'})

    return doc_contents_df


def split_contents(x):
    """Split contents into number of chunks defined by split_factor
    e.g. if split factor = 2 then split contents into 2 chunks
    """
    thres = int(len(x['contents'])/x['split_factor'])

    return [x['contents'][i:i+thres] for i in range(0, len(x['contents']), thres)]


def split_pages(pages_df):
    """Split pages that are too long for the model
    prepare the contents to be embedded
    """
    # For instances with token count > token_thres, split them so they fit model threshold so we could get their embeddings
    # Calculate split factor for each chapter
    pages_df['split_factor'] = 1
    pages_df.loc[pages_df['num_tokens_oai']>prm.TOKEN_THRES, 'split_factor'] = round(
        pages_df['num_tokens_oai']/prm.TOKEN_THRES, 0
        )

    # Split contents
    pages_df['contents_split'] = pages_df.apply(
        lambda x: split_contents(x), axis=1
        )

    # Explode the split contents
    pages_contents_long_df = pages_df.explode(
        column='contents_split'
    )[['contents_split']]

    # Create a token count column (Again - this time for long table)
    pages_contents_long_df['num_tokens_oai'] = pages_contents_long_df['contents_split'].apply(
        lambda x: num_tokens_from_messages([{'message': x}])
    )

    ## Drop rows where num_tokens_oai is less than 25
    pages_contents_long_df = pages_contents_long_df[pages_contents_long_df['num_tokens_oai'] > 25].copy()
    
    return pages_contents_long_df


def prepare_for_embed(pages_df, collection_name):
    """Pre-process pages to be embedded
    returns a dataframe with the following columns:
    name, interaction_type, text, text_token_no, page, timestamp
    """
    # Form text column for each fragment
    pages_df['text'] = "PAGE: " + pages_df.index.astype(str) + " CONTENT: " + pages_df['contents_split']

    # Further dataframe processing
    return (
        pages_df
        .drop(columns=['contents_split']) # Drop contents_split column
        .reset_index() # Reset index so chapter names are stored in columns
        .rename(columns={'index': 'page', 'num_tokens_oai': 'text_token_no'}) # Rename index column to chapter
        .assign(name=collection_name) # Add session_name column
        .assign(interaction_type='source') ## Add interaction type column
        .assign(timestamp=0) # Add timestamp column
        [['name', 'interaction_type', 'text', 'text_token_no', 'page', 'timestamp']]
    )


def embed_cost(pages_contents_long_df, price_per_k=0.0004):
    """Calculate the cost of running the model to get embeddings"""
    embed_cost = (pages_contents_long_df['text_token_no'].sum() / 1000) * price_per_k
    return embed_cost


def embed_pages(pages_contents_long_df):
    """Get embeddings for each page"""
    # Get embeddings for each page
    pages_contents_long_df['embedding'] = pages_contents_long_df['text'].apply(
        lambda x: pickle.dumps(get_embedding(x))
    )
    return pages_contents_long_df


def convert_table_to_dct(table):
    """Converts table to dictionary of embeddings
    As Pandas df.to_dict() makes every value a string we need to convert it to list of loats before passing it to the model
    """
    table_dct = table[['embedding']].to_dict()['embedding']
    for k, v in table_dct.items():
        table_dct[k] = ast.literal_eval(v)
    return table_dct




def prepare_chat_recall(chat_table):
    """Prepare chat recall table for chatbot memory
    """
    usr_f = (chat_table['interaction_type'] == 'user')
    ast_f = (chat_table['interaction_type'] == 'assistant')
    
    return chat_table[usr_f], chat_table[ast_f]
