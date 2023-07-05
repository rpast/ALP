"""Functions that handle chatbot interactions.
"""

import openai
import pandas as pd
import ai_tools as oai
import params as prm

class Chatbot:

    def __init__(self):
        self.sys_message = {
            'role': 'system',
            'content':  """
                You are a helpful assistant. You provide only factual information. 
                When you do not know the answer, you say it. Wherever you can, you provide sources.
                I will provide my query after INP tag, and the context you will use in your answer after following tags: 
                SRC - context from source text we are talking about; 
                QRY - one of previous inputs from current conversation that may be relevant to the current INP; 
                RPL - one of your previous replies from current conversation that may be relevant to current INP.
            """
        }

    def build_prompt(self, 
                    prev_usr, 
                    prev_asst, 
                    recall_src, 
                    recall_usr, 
                    recall_ast, 
                    question):
        """Builds prompt for the chatbot.
        Returns a list of dicts
        """

        self.prev_user = {"role": "user", "content": f"{prev_usr}"}
        self.prev_assistant = {"role": "assistant", "content": f"{prev_asst}"}
        self.user_message = {
            "role": "user", 
            "content": f"SRC: {recall_src}. QRY: {recall_usr}. RPL: {recall_ast}. INP: {question}"
            }

        return [self.sys_message, self.prev_user, self.prev_assistant, self.user_message]
    

    def chat_completion_response(self, msg):
        """Makes API call to OpenAI's chat completion endpoint.
        """

        #TODO: user can choose variant of GPT model
        api_response = openai.ChatCompletion.create(
            model=prm.OPENAI_MODEL_16K,
            messages=msg
        )

        return api_response
    
    def retrieve_closest_idx(self, q, n, src, usr, ast):
        """Retrieves n closest samples from recall tables.
        Acts as a simple nearest neighbors search with cosine similarity.
        """

        self.recall_source_idx = None
        self.recall_user_idx = None
        self.recall_assistant_idx = None

        ## Get SRC context
        if len(src) == 0:
            print('WARNING! No source material found.')
            self.recall_source_idx = []
        else:
            # Get the context most relevant to user's question
            recall_source_id = oai.order_document_sections_by_query_similarity(q, src)[0:n]
            if len(recall_source_id)>1:
                # If recal source id is a list n>1, join the text from the list
                self.recall_source_idx = [x[1] for x in recall_source_id]
            else: 
                # Otherwise just get the text from the single index
                self.recall_source_idx = recall_source_id[1]

        ## GET QRY context
        # We get most relevant context from the user's previous messages here
        if len(usr) == 0:
            print('No context found in user chat history')
            self.recall_user_idx = []
        else:
            self.recall_user_idx = oai.order_document_sections_by_query_similarity(q, usr)[0][1]

        ## GET RPL context
        # We get most relevant context from the agent's previous messages here
        if len(ast) == 0:
            print('No context found agent chat history')
            self.recall_assistant_idx = []
        else:
            self.recall_assistant_idx = oai.order_document_sections_by_query_similarity(q, ast)[0][1]


    def retrieve_text(self, src, chat):
        self.src_text = 'No source text found'
        self.usr_text = 'No user text found'
        self.ast_text = 'No assistant text found'


        if self.recall_source_idx:
            if self.recall_source_idx != []:
                self.src_text = src.loc[self.recall_source_idx, 'text'].tolist()
                self.src_text = '| '.join(self.src_text)


        if self.recall_user_idx:
            if self.recall_user_idx != []:
                self.usr_text = chat.loc[self.recall_user_idx]['text']


        if self.recall_assistant_idx:
            if self.recall_assistant_idx != []:
                self.ast_text = chat.loc[self.recall_assistant_idx]['text']

        return self.src_text, self.usr_text, self.ast_text
        


