"""Functions that handle chatbot interactions.
"""

import openai

class Chatbot:
    def __init__(self):
        self.sys_message = {
            'role': 'system',
            'content': "You are a helpful assistant. You provide only factual information. If you do not know the answer, you say it. I provide my input after INP tag."
        }

    def chat_completion_response(self, question):
        user_message = {
            "role": "user",
            "content": f"INP: {question}"
        }

        messages = [
            self.sys_message, 
            user_message
            ]

        api_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        return api_response['choices'][0]['message']['content']