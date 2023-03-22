import tiktoken, openai
import numpy as np

# Count tokens for each chapter
def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages.
    """
    
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(f"""
        num_tokens_from_messages() is not presently implemented for model {model}.
        See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.
        """)


# Build simple embedding function
def get_embedding(text, model="text-embedding-ada-002"):
    """Returns the embedding for a given text.
    """
    return openai.Embedding.create(
        input=text, 
        model=model,
        )['data'][0]['embedding']

def vector_similarity(x, y):
    """
    Returns the similarity between two vectors.
    
    Because OpenAI Embeddings are normalized to length 1, the cosine similarity is the same as the dot product.
    """

    # Catch all ys that are not lists or arrays
    if not isinstance(y, (list, np.ndarray)):
        return 0

    x = np.array(x, dtype=np.float32)
    y = np.array(y, dtype=np.float32)


    if len(x) < len(y):
        # pad x with zeros to match the length of y
        x = np.concatenate([x, np.zeros(y.shape[0] - x.shape[0], dtype=np.float32)])
    elif len(y) < len(x):
        # pad y with zeros to match the length of x
        y = np.concatenate([y, np.zeros(x.shape[0] - y.shape[0], dtype=np.float32)])

    # Make sure I return single scalar value


    return np.dot(x,y)


def order_document_sections_by_query_similarity(query, contexts):
    """
    Find the query embedding for the supplied query, and compare it against all of the pre-calculated document embeddings
    to find the most relevant sections. 
    
    Return the list of document sections, sorted by relevance in descending order.
    """
    query_embedding = get_embedding(query)
    
    document_similarities = sorted(
        [
            (vector_similarity(query_embedding, doc_embedding), doc_index) for doc_index, doc_embedding in contexts.items()
            ], reverse=True
        )
    
    return document_similarities