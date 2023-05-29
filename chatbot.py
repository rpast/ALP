"""Functions that handle chatbot interactions.
"""

import openai
import pandas as pd

class Chatbot:
    def __init__(self):
        self.sys_message = {
            'role': 'system',
            'content':  "You are a helpful assistant. You provide only factual information. When you do not know the answer, you say it. I will provide my input after INP tag. I will pass the context you will use in your answer. I encode it with following tags: SRC - context coming from source document, article, book, text we are talking about; QRY - one of previous inputs I passed to you in current conversation; RPL - one of your previous replies to my questions from current conversation."
        }

    def build_prompt(self, 
                    prev_usr, 
                    prev_agnt, 
                    recall_src, 
                    recall_usr, 
                    recall_ast, 
                    question):
        """Builds prompt for the chatbot.
        """

        self.prev_user = {"role": "user", "content": f"{prev_usr}"}
        self.prev_assistant = {"role": "assistant", "content": f"{prev_agnt}"}
        self.user_message = {
            "role": "user", 
            "content": f"SRC: {recall_src}. QRY: {recall_usr}. RPL: {recall_ast}. INP: {question}"
            }

        return [self.sys_message, self.prev_user, self.prev_assistant, self.user_message]
    

    def chat_completion_response(self, msg):
        """Makes API call to OpenAI's chat completion endpoint.
        """

        api_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=msg
        )

        return api_response
    

# Create Session class that handles separate colelctions and chat history.
class Session:
    """Manages Session state
    """

    def __init__(self, session_table) -> None:

        # TODO: test if ~collection_uuid are unique
        self.session_uuid = session_table['uuid'].unique()[0]
        self.collection_uuid = session_table['collection_uuid'].unique().tolist()
        self.chat_uuid = session_table['chat_uuid'].unique()[0]
        self.session_name = session_table['session_name'].unique()[0]
        self.session_date = session_table['session_date'].unique()[0]
    
    def __repr__(self) -> str:
        return f"""
            Session: {self.session_name} ({self.session_uuid}); 
            Date: {self.session_date}; 
            Collections: {self.collection_uuid}; 
            Chat: {self.chat_uuid}
            """