import re
from PyPDF2 import PdfReader
from pathlib import Path
import pandas as pd

import params as prm
from oai_tool import num_tokens_from_messages



## Functions
def load_pdf():
    # Get the document name from the user
    doc_name = input('Enter document name from input: ')

    # Extract the text from the PDF and split it by page
    pdf_text = extract_text_by_page(Path(f'./input/{doc_name}'))

    # Display the extracted text
    # for page_number, content in pdf_text.items():
    #     print(f"Page {page_number}: {content}\n")
    return pdf_text
#
def extract_text_by_page(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        reader = PdfReader(pdf_file)
        num_pages = len(reader.pages)
        pdf_text = {}

        for page_number in range(num_pages):
            page = reader.pages[page_number]
            text = page.extract_text()
            cleaned_text = clean_text(text)
            pdf_text[page_number+1] = cleaned_text

    return pdf_text
#
def clean_text(text):
    text = text.replace('\t', ' ')
    text = text.strip().lower()
    text = text.replace('\n', '')
    text = text.replace('\t', '')
    text = re.sub(r'\s+', ' ', text)
    return text



doc_contents = load_pdf()

# Grab contents into a dataframe
doc_contents_df = pd.DataFrame(doc_contents).T

# Create a token count column
doc_contents_df['num_tokens_oai'] = doc_contents_df['contents'].apply(
    lambda x: num_tokens_from_messages([{'message': x}])
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