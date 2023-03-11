# Project notes

## General wishes
1. User can define the number of text snippets to use as a context in a conversation.
   This limits the context window of the whole conversation.
2. Monitor context window of the conversation.
3. User can peek used context snippets anytime.
4. Deal with sumarrization queries of the whole corpus

## DB
0. Save session details in a dedicated table
1. Every API call and response gets saved in the database