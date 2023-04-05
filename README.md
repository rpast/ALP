# ALP

_ALP is an open-source, knowledge-grounded conversational AI system designed to generate responses grounded in relevant knowledge from external sources._ 📖💫

ALP is currently in development, but it can be used locally on users' machines. Built with simplicity in mind, ALP reads chosen PDF file, has unlimited conversational memory and the ability to export conversation and source embeddings in JSON format.

ALP stores conversation history and embeddings in local SQLite database 🗄️. Thanks to that document upload and embedding process happens only once. In future releases user will get more functionalities to manage conversation history. 

ALP is intended to be run locally on users machines 💻. All is needed is Python and few commands in your command line. Feel free to fork, explore the code, hack it and adjust to your needs 🔧. 

## Table of Contents

- [ALP](#alp)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Features](#features)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Usage](#usage)
  - [Demo](#demo)
  - [Todo](#todo)

## Introduction
ALP is designed to enhance the accuracy of responses of GPT-3.5 model related to a specific PDF document by using a retrieval augmentation technique. This approach ensures that the most relevant context is always provided to the model with user's question. ALP was created to help me manage the overwhelming knowledge base of research papers, books and notes, making it easier to access crucial information without having to read through everything.

Currently ALP utilizes following models:
1. ```text-embedding-ada-002```
2. ```gpt-3.5-turbo```. 

## Features
- **Conversational research assistant**: Interact with and get information from loaded PDF files.
- **Unlimited conversational memory**: Retain information from previous conversations for context-aware responses.
- **User can come back to past conversations**: Pick up your convo right where you left. 
- **Support for long documents**: You can upload books. The only thing that limits you is your API limit.
- **JSON export**: Export conversation and source embeddings as JSON format.
- **Retrieval augmentation**: Utilize retrieval augmentation techniques for improved accuracy. Read more [here](https://arxiv.org/pdf/2104.07567.pdf).
- **Local deployment**: Spin up ALP locally on your machine for privacy, convenience and hackability. 
- **Open source**: The code is yours to read, test and break. 

## Installation
To set up ALP on your local machine, follow these steps:

1. **Install Python:**

Make sure you have Python installed on your machine. We recommend installing [Anaconda](https://www.anaconda.com/products/distribution) for an easy setup, although it may not be the most resource-efficient option.

2. **Clone the repository:**

```bash 
git clone https://github.com/yourusername/alp.git 
cd alp
```

3. **Create a virtual environment and activate it:**

```bash 
python3 -m venv venv 
source venv/bin/activate
```

For Windows users:

```bash
python -m venv venv 
venv\Scripts\activate
```

4. **Install the required dependencies:**

```bash
pip install -r requirements.txt
```

## Configuration
By default, ALP runs on `localhost`


## Usage
5. **Run the ALP application:**

```bash
python alp.py
```

6. **Access the application:**
   
The app should open in your default web browser. If it doesn't, navigate to http://localhost:5000.

7. **Start using ALP:**

Welcome page is the one where you 1) either set your session name and upload pdf file 2) or choose a session name from the ones available in drop-down menu. 
For both cases in order for ALP to work you have to pass Open AI API key. Since this is a local environment you are safe to do so. You can also inspect the code to see that nothing fishy is happening with your key.

To get API key you have to create an account on https://platform.openai.com 🌐. As a new user you will get a few bucks to test API capabilities. This should be enough for a couple of hundred regular exchanges with ALP.

<img src="https://github.com/rpast/ALP/blob/master/static/alp_welcome.png?raw=true" width="450px" height="350px"></img>

After you hit "Start Session" button:
1. If you chose an existing conversation from a dropdown menu, you will be moved to chat interface.
2. If you defined a new session name and selected a .pdf to upload, you will be moved to a *Summary* page where you will see:
   1. Session name
   2. Number of pages that the app will send for embedding. This number may be larger than the number of pages in uploaded document since ALP splits pages if they happen to be dense with tokens. 
   3. Estimated $ cost of embedding

  After hitting 'Proceed', ALP starts embedding process that will take around a minute (for longer documents it will take proportionally longer). After the process is complete you will be moved to the chat interface.

Anytime in the conversation you can get back to *Welcome* to start a new conversation. The whole exchange is automatically saved in the local database located under *./static/data/dbs/* 

## Demo
<img src="https://github.com/rpast/ALP/blob/master/static/alp_demo.gif?raw=true"></img>


## Todo
1. [x] Allow user to continue conversations on another sessions.
   1. [ ] User can clean-up the conversation leaving only embeddings in the conversation hisory.
   2. [ ] User can delete unwanted converastions from database.
2. [ ] Display sources used by the agent for the answer.
3. [ ] Allow user to upload more than one document
4. [ ] User is able to upload text from other sources 
5. [ ] Implement alternative embedding models
6. [ ] Implement models for ai content detection
