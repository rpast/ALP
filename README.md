# ALP

ALP is an open-source, knowledge-grounded conversational AI system designed to generate responses grounded in relevant knowledge from external sources.
ALP is currently in development, but it can be used locally on users' machines. Built with simplicity and efficiency in mind, ALP reads chosen PDF file, has unlimited conversational memory and the ability to export conversation and source embeddings in JSON format.

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
- **Support for long documents**: You can upload books. The only thing that limits you is your API limit.
- **JSON export**: Export conversation and source embeddings as JSON format.
- **Retrieval augmentation**: Utilize retrieval augmentation techniques for improved accuracy. Read more [here](https://arxiv.org/pdf/2104.07567.pdf).
- **Local deployment**: Spin up ALP locally on your machine for privacy and convenience.

## Installation
To set up ALP on your local machine, follow these steps:

1. **Install Python:**

Make sure you have Python installed on your machine. We recommend installing [Anaconda](https://www.anaconda.com/products/distribution) for an easy setup, although it may not be the most resource-efficient option.

2. **Clone the repository:**

\```bash
git clone https://github.com/yourusername/alp.git
cd alp
\```

3. **Create a virtual environment and activate it:**

\```bash python3 -m venv venv
source venv/bin/activate
\```

For Windows users:

\```bash
python -m venv venv
venv\Scripts\activate
\```

4. **Install the required dependencies:**

\```bash
pip install -r requirements.txt
\```

## Configuration
By default, ALP runs on `localhost`


## Usage
5. **Run the ALP application:**

\```bash
python alp.py
\```

6. **Access the application:**
   
The app should open in your default web browser. If it doesn't, navigate to http://localhost:5000.

7. **Start using ALP:**

Provide a session name, API key, and select PDF for upload to start interacting with the conversational research assistant.

## Demo
<img src="https://github.com/rpast/ALP/blob/master/static/alp_demo_webapp.gif?raw=true"></img>


## Todo
1. [ ] Allow user to continue conversations on another sessions.
2. [ ] Display sources used by the agent for the answer.
3. [ ] Allow user to upload more than one document
4. [ ] User is able to upload text from other sources 
5. [ ] Implement alternative embedding models
6. [ ] Implement models for ai content detection
