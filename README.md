# ALP

_Work in progress_

Conversational research assistant with ADA and GPT3.5


## Features
1. Automated pdf content preprocessing.
2. Accurate context building through nearest neighbors context selection with embedding vectors on passed source material.
3. Conversation history stored in local SQLite db.
4. System holds memory of past conversations and makes use of it in the conversation.

## Models used
1. ```text-embedding-ada-002```
2. ```gpt-3.5-turbo```. 

## Sample usage

<img src="https://github.com/rpast/ALP/blob/master/static/alp_demo_webapp.gif?raw=true"></img>


## Todo
1. [x] Inject origin conversation context to the interaction database
2. [x] Hold latest exchange in the context, so the model is able to retrieve it without nearest neighbors on embedding space
3. [x] Count tokens in the context window and display to user
4. [x] Refactor code into .py script 
5. [x] Wrap the code into Flask app
   1. [x] PDF upload and preprocessing.
   2. [x] Count embedding costs and embedding step before moving to chat
      1. [x] use database to pass data between functions
   3. [x] Add context handler in the chat
   4. [ ] Fix session name formatting (account for ' ' and '-')
   5. [ ] Set a dedicated dir to store .db
   6. [ ] Test for session exclusive database
   7. [ ] Implement safe way of handling user's api keys
   8. [ ] Allow for context table extract (to JSON)
6. [x] Test on longer pdfs (books)
   1. [ ] Refactor embedding function so it sends no more than {{limit}} api calls per minute
   2. [ ] Add a way to chop the source material into arbitrary number of chunks
   3. [ ] Implement huggingface embedding model
7. [ ] Implement whisper audio-to-text module