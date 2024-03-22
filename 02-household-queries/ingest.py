from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.llms import GPT4All
from langchain import LLMChain

from langchain_community.document_loaders import JSONLoader, PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.vectorstores import Chroma
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
import json
import os
from pathlib import Path
from pprint import pprint
import dotenv

# Implementation with Google Gemini embeddings and storing in Chroma
# dotenv.load_dotenv()
# #Load the models
# GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

# llm = ChatGoogleGenerativeAI(model="gemini-pro",
#                              verbose = True,temperature = 0.1,google_api_key=GOOGLE_API_KEY)
# embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Load the PDF and create chunks
# download from https://nava.slack.com/archives/C06ETE82UHM/p1710880671273909?thread_ts=1710880610.675809&cid=C06ETE82UHM
# loader = PyPDFLoader("./7_cfr_part_272__up_to_date_as_of_3-15-2024_.pdf")
# vectordb=Chroma.from_documents(pdf_pages,embeddings)

# pdf_pages = loader.load_and_split(text_splitter)

#Configure Chroma as a retriever with top_k=5
# retriever = vectordb.as_retriever(search_kwargs={"k": 5})

#Create the retrieval chain
# template = """
# You are a helpful AI assistant.
# Answer based on the context provided. 
# context: {context}
# input: {input}
# answer:
# """
# prompt = PromptTemplate.from_template(template)
# combine_docs_chain = create_stuff_documents_chain(llm, prompt)
# retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

# Invoke the retrieval chain
# response=retrieval_chain.invoke({"input":"what are appeals?"})

# Print the answer to the question
# print(response["answer"])


# Load the json and create chunks
# download from https://drive.google.com/file/d/1UoWmktXS5nqgIWj2x_O5hgzwU0yVuaJc/view
guru_file_path='./guru_cards_for_nava.json'


text_splitter = CharacterTextSplitter(
    chunk_size=350,
    chunk_overlap=200,
)

embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
json_data = JSONLoader(
    file_path=guru_file_path,
    jq_schema='.[].content',
    text_content=False)

guru_data = json_data.load()


#Turn the chunks into embeddings and store them in Chroma
vectordb=Chroma.from_documents(guru_data,embedding_function)

#Configure Chroma as a retriever with top_k=5
retriever = vectordb.as_retriever(search_kwargs={"k": 5})

#Create the retrieval chain
template = """
You are a helpful AI assistant.
Answer based on the context provided. 
context: {context}
input: {input}
answer:
"""

gpt4all_path= "./mistral-7b-instruct-v0.1.Q4_0.gguf"
llm = GPT4All(model=gpt4all_path,max_tokens=1000, verbose=True,repeat_last_n=0)
prompt = PromptTemplate.from_template(template)
llm_chain = LLMChain(prompt=prompt, llm=llm)
combine_docs_chain = create_stuff_documents_chain(llm, prompt)
retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

# Invoke the retrieval chain
response=retrieval_chain.invoke({"input":"what are appeals?"})

print(response)
