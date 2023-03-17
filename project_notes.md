# Project notes

## General wishes
1. [ ] User can define the number of text snippets to use as a context in a conversation.
   This limits the context window of the whole conversation.
2. [x] Monitor context window of the conversation.
3. [ ] User can peek used context snippets anytime. 
4. [ ] Deal with sumarry queries of the whole corpus
5. [ ] User can upload more than one pdf
6. [ ] User can upload other filetypes than pdf (txt, md, docx etc.)

## DB
0. [x] Save session details in a dedicated table
1. [x] Every API call and response gets saved in the database


## Web app
1. [ ] PoC for basic conversational interface (chat window, db handler, call-response)
2. [ ] Display uploaded document
3. [ ] Ability to jump to sampled pages
4. [ ] User can export the conversation to json