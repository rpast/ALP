# TSunset

PoC for conversational research assistant with ADA and GPT3.5

Sources:
How_to_format_inputs_to_ChatGPT_models: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_format_inputs_to_ChatGPT_models.ipynb

Question_answering_using_embeddings: https://github.com/openai/openai-cookbook/blob/main/examples/Question_answering_using_embeddings.ipynb

## Sample usage:

1. User loads the document and preprocesses it to a form of a chapter-sized chunks.
2. Each chunk gets its embedding from ```text-embedding-ada-002```
3. User's query gets measured against chunks and the one with the lowest distance score gets chosen (cosine distance).
4. Closest chunk and query get injected into the input for API call to ```gpt-3.5-turbo```. 

<img src="https://github.com/rpast/tsunset/blob/master/static/tsun_poc.png?raw=true"></img>


## Todo

1. [ ] Implement session memory so longer conversations with arbitrary context are possible.
2. [ ] Come up with complexity control of the API call.
3. [ ] Refactor document pre-processing so as little input from user is necessary.
