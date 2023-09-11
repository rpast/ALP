# ALP

## Version information

This is a second iteration of the script. New features include:
* New data model that decouples sessions (chat conversations) and collections (pdf resources). Thanks to that, user session can point to one or more pdf resource. Also, altering the conversation does not affect the embbeddings stored in the database. 
* [SBERT](https://www.sbert.net/) provides embedding model instead of Open AI. This reduces costs and increases performance. Open AI's Ada left as a legacy model. 

_1st iteration version bak on ALP_1st_iter_bak branch_

## Overview

_ALP is an open-source, knowledge-grounded conversational AI system designed to generate responses grounded in relevant knowledge from external sources._ 📖💫

ALP is currently in development, but it can be used locally on users' machines. Built with simplicity in mind, ALP reads chosen PDF file, has unlimited conversational memory and the ability to export conversation and source embeddings to JSON format.

ALP stores conversation history and embeddings in local SQLite database 🗄️. Thanks to that document upload and embedding process happens only once. This also allows a user to continue conversations.

ALP is intended to be run via localhost 💻. All you need is Python and few commands to setup environment. Feel free to fork, explore the code, and adjust to your needs 🔧. 

## Table of Contents

- [ALP](#alp)
  - [Table of Contents](#table-of-contents)
  - [Changelog](#changelog)
  - [Introduction](#introduction)
  - [Features](#features)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Usage](#usage)
  - [Demo](#demo)
  - [Todo](#todo)

## Changelog
- 20230705 - new data model, SBERT based embeddings
- 20230411 - interface upgrade, UX improvements, bugfixes
- 20230406 - bug-fix that prevented program to initialize database under /static/data/dbs/; requirements.txt fix
- 20230405 - program stores converastion history
- 20230911 - user can define custom agent behavior and choose them from the drop-down menu in session manager.

## Introduction
ALP enhances the accuracy of responses of GPT-based models relative to given PDF documents by using a retrieval augmentation method. This approach ensures that the most relevant context is always passed to the model as a context to user's question. The intention behind ALP is to assist the overwhelming knowledge base of research papers, books and notes, making it easier to access and digest content.

Currently ALP utilizes following models:
1. Text embedding: ```multi-qa-MiniLM-L6-cos-v1```
2. Generation: ```gpt-3.5-turbo```. 

## Features
- **Conversational research assistant**: Interact with and get information from collections of pdf files.
- **Unlimited conversational memory**: Retain information from previous conversations for context-aware responses.
- **Come back to past conversations**: Pick up your conversation right where you left. 
- **Flexible data model**: Allows for conversation with more than one document in one session.
- **Uses open source models**: [Sentence-Transformers](https://www.sbert.net/) allow for costless and fast text embedding.
- **Support for long documents**: You can upload long texts. It takes ~10 minutes to embed ~300 page document. 
- **JSON export**: Export conversation as a JSON file.
- **Retrieval augmentation**: Utilize retrieval augmentation techniques for improved accuracy. Read more [here](https://arxiv.org/pdf/2104.07567.pdf).
- **Define your own agent behavior**: set system message defining your agents in ./static/data/simulacra.json. You can then easily adjust html form to choose names from a drop-down menu. 
- **Local deployment**: Spin up ALP locally on your machine.
- **Open source**: The code is yours to read, test and break and build upon. 

## Installation
To set up ALP on your local machine, follow these steps:

1. **Install Python:**

Make sure you have Python installed on your machine. I recommend [Anaconda](https://www.anaconda.com/products/distribution) for an easy setup.

__Important:__ ALP runs on Python 3.10

2. **Fork and clone the repository:**

After forking the repo clone it in a command line:

```bash 
git clone https://github.com/yourusername/alp.git 
cd ALP
```

3. **Create a virtual environment and activate it:**

From within the ALP/ local directory invoke following commands

For Linux users in Bash:

```bash 
python3 -m venv venv
source venvname/bin/activate
```

For Windows users in CMD:

```
python -m venv venv
venvname\Scripts\activate.bat
```

This should create ALP/venv/ directory and activate virtual environment.
Naturally, you can use other programs to handle virtualenvs.

4. **Install the required dependencies to virtual environment:**

```bash
pip install -r requirements.txt
```

## Configuration
By default, ALP runs in `localhost`. It requires API key to connect with GPT model via Open AI API. 
in the ALP/ directory create an api_key.txt and paste your API key there. You can get your API key here https://platform.openai.com 🌐


## Usage
5. **Run the ALP application:**

```bash
python alp.py
```

6. **Access the application:**
   
The app should open in your default web browser. If it doesn't, navigate to http://localhost:5000.
First use involves creation of app.db file under ALP/static/data/dbs/. This is your SQLite database file that will hold conversation history and embeddings. Also, the script will download _'multi-qa-MiniLM-L6-cos-v1'_ (80 MB) to your PC from Hugging Face repositories. It will happen only once.


7. **Start using ALP:**

ALP app interface consists of couple of sections:

* ALP - HUB allows you to create new collection under 'Collections' or create/continue conversation session under 'Sessions'.
* In ALP - COLLECTIONS MANAGER you can create a new collection by specifying its name and uploading a pdf file. 
* In ALP - SESSION MANAGER you can continue existing session by selecting it from dropdown and hitting 'Start'. You can create a new session there as well by defining its name and selecting collections linked to the session.
* In ALP - SESSION window you can have a conversation over collections linked to the session. Each time a similarity score is calculated between user's query and collections' embeddings, a list of most similar datasources is printed in the program's console. These sources will be passed as a context with the user's question to the GPT model.

## Screenshots
<img src='https://github.com/rpast/ALP/blob/dmodel_updt/static/alp-hub.png?raw=true' width='600'></src>
<br>
<img src='https://github.com/rpast/ALP/blob/dmodel_updt/static/alp-session-mgr.png?raw=true' width='600'></src>
<br>
<img src='https://github.com/rpast/ALP/blob/dmodel_updt/static/chat1.png?raw=true' width='600'></src>
<br>
<img src='https://github.com/rpast/ALP/blob/dmodel_updt/static/chat2.png?raw=true' width='600'></src>
<br>
<img src='https://github.com/rpast/ALP/blob/master/static/chat3.png?raw=true' width='600'></src>



## Todo
- [x] Allow user to continue conversations on another sessions.
- [x] Save chat history in separate table
- [x] Upload document into context table
- [x] Allow user to choose context for conversation, or continue the previous one
- [x] Implement alternative embedding models (sentence-transformers)
- [x] Allow user to upload more than one document
- [x] Decouple conversation data from collection data
- [x] Implement Sentence-Transformers for text embedding
- [x] Display sources used by the agent for the answer
- [x] Introduce various agents in the chatbot
- [ ] User can delete unwanted converastions from database
- [ ] User is able to upload text from sources other than pdf
- [ ] Improve GUI design
- [ ] Add Whisper for audio-text
