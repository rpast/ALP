"""Content processing utilities
"""

import re 
import uuid
import pickle
import pandas as pd

import lib.params as prm

from lib.ai_tools import get_embedding_gpt, get_embedding_sbert, get_tokens, decode_tokens


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
    """Convert dictionary of pages to Pandas dataframe"""
    pages_dct = pages_to_dict(pages)
    # # Grab contents into a dataframe
    doc_contents_df = pd.DataFrame(pages_dct, index=['contents']).T

    return doc_contents_df


def split_pages(pages_df, method):
    """Split pages that are too long for the model
    prepare the contents to be embedded
    """

    pages_df['contents_tokenized'] = pages_df['contents'].apply(
            lambda x: get_tokens(x, method=method)
        )

    # We want to split the contents_tokenized by counting the number of tokens and when it reaches the threshold, split it
    pages_df['contents_tokenized'] = pages_df['contents_tokenized'].apply(
        lambda x: [x[i:i+prm.TOKEN_THRES] for i in range(1, len(x), prm.TOKEN_THRES)]
    )

    # At this point the tokenized text is split by set threshold into an n element list
    # We want to explode that list into rows and perserve index that tracks the src page
    pages_contents_long_df = pages_df.explode(
        column='contents_tokenized'
    )[['contents_tokenized']]

    # track # of tokens in each text snippet
    pages_contents_long_df['text_token_no'] = pages_contents_long_df['contents_tokenized'].apply(
        lambda x: len(x)
    )

    # decode tokens back into text (SBERT default)
    pages_contents_long_df['contents'] = pages_contents_long_df['contents_tokenized'].apply(
        lambda x: decode_tokens(x, method=method)
    )

    return pages_contents_long_df


def prepare_for_embed(pages_df, collection_name, model):
    """Pre-process dataframe that holds src pages to be embedded by chosen model
    returns a dataframe with the following columns:
    name, interaction_type, text, text_token_no, page, timestamp
    """

    return_cols=['name', 'interaction_type', 'text', 'text_token_no', 'page', 'timestamp', 'embedding_model']

    # Further dataframe processing
    pages_df = (
        pages_df
        .reset_index() # Reset index so page numbers get stored in column
        .rename(columns={'index': 'page'})
        .assign(name=collection_name)
        .assign(interaction_type='source')
        .assign(timestamp=0)
        .assign(embedding_model=model)
    )
    # Form text column for each fragment, we will later use it as the source text for embedding
    pages_df['text'] = "SRC:" + pages_df['name'] + "PAGE: " + pages_df.index.astype(str) + " CONTENT: " + pages_df['contents']

    return pages_df[return_cols]


def embed_cost(pages_contents_long_df, price_per_k=0.0004):
    """Calculate the cost of running the Open AI model to get embeddings
    """
    embed_cost = (pages_contents_long_df['text_token_no'].sum() / 1000) * price_per_k
    return embed_cost


def embed_pages(pages_contents_long_df, method):
    """Get embeddings for each page"""

    # Get embeddings for each page
    if method == 'openai':
        print(f'!Sending pages to Open AI for embedding with {prm.OPENAI_MODEL}')
        pages_contents_long_df['embedding'] = pages_contents_long_df['text'].apply(
            lambda x: pickle.dumps(get_embedding_gpt(x))
        )
    elif method == 'SBERT':
        print(f'!Embedding pages with {prm.SENTENCE_TRANSFORMER_MODEL}')
        pages_contents_long_df['embedding'] = pages_contents_long_df['text'].apply(
            lambda x: pickle.dumps(get_embedding_sbert(x))
        )

    return pages_contents_long_df


def convert_table_to_dct(table):
    """Converts table to dictionary of embeddings
    As Pandas df.to_dict() makes every value a string, 
    we need to convert it to list of floats before passing it to the model
    """
    table_dct = table[['embedding']].to_dict()['embedding']
    for k, v in table_dct.items():
        # table_dct[k] = ast.literal_eval(v)
        table_dct[k] = v
    return table_dct


def prepare_chat_recall(chat_table):
    """Prepare chat recall table for chatbot memory build
    """
    usr_f = (chat_table['interaction_type'] == 'user')
    ast_f = (chat_table['interaction_type'] == 'assistant')
    
    return chat_table[usr_f], chat_table[ast_f]

def format_response(response):
    """Grab generator response and format it for display in the chatbot
    :param response: dict
    """
    code_pattern = r'```(.*?)```'
    cont = response['choices'][0]['message']['content']

    # Replace newlines with <br> tags
    cont_interim = cont.replace('\n', '<br>')
    
    # Use a lambda function to replace detected code with code wrapped in <pre> tags
    new_cont = re.sub(code_pattern, lambda match: '<pre>' + match.group(1) + '</pre>', cont_interim, flags=re.DOTALL)

    return new_cont
