from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.llms import GPT4All
from langchain import LLMChain
from bs4 import BeautifulSoup
from langchain_community.document_loaders import JSONLoader, PDFMinerLoader
from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.vectorstores import Chroma
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
import json
import os
from pathlib import Path
from pprint import pprint
import dotenv
import requests

dotenv.load_dotenv()

# Load the models
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
llm = ChatGoogleGenerativeAI(model="gemini-pro",
                             verbose = True,google_api_key=GOOGLE_API_KEY)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# initialize chroma db
vectordb=Chroma(embedding_function=embeddings)

# Load the PDF and create chunks
# download from https://nava.slack.com/archives/C06ETE82UHM/p1710880671273909?thread_ts=1710880610.675809&cid=C06ETE82UHM
loader = PDFMinerLoader("./7_cfr_part_272__up_to_date_as_of_3-15-2024_.pdf")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=500)
pdf_pages = loader.load_and_split(text_splitter)

vectordb.add_documents(pdf_pages)
# Load the json and create chunks
# download from https://drive.google.com/file/d/1UoWmktXS5nqgIWj2x_O5hgzwU0yVuaJc/view
guru_file_path='./guru_cards_for_nava.json'

# GURU_ENDPOINT = "https://api.getguru.com/api/v1/"
# def get_guru_data():
#     url = f"{GURU_ENDPOINT}cards/3fbff9c4-56a8-4561-a7d1-09727f1b4703"
#     headers = {
#     'Authorization': os.environ.get('GURU_TOKEN')}
#     response = requests.request("GET", url, headers=headers)
#     return response.json()

def get_text_chunks_langchain(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=500)
    texts = text_splitter.split_text(text)
    docs = [Document(page_content=t) for t in texts]
    return docs

json_data = JSONLoader(
    file_path=guru_file_path,
    jq_schema='.[].content',
    text_content=False)

guru_data = json_data.load()

guru_data_contents = ""
for content in guru_data:
    soup = BeautifulSoup(content.page_content, "html.parser")
    text = soup.get_text(separator='\n', strip=True)
    guru_data_contents += f" {text} "

chunks = get_text_chunks_langchain(guru_data_contents)
vectordb.add_documents(chunks)

retriever = vectordb.as_retriever(search_kwargs={"k": 1})

# Create the retrieval chain
template = """
You are a helpful AI assistant.
Answer based on the context provided. 
context: {context}
input: {input}
answer:
"""

# Open source option
# gpt4all_path= "./mistral-7b-instruct-v0.1.Q4_0.gguf"
# llm = GPT4All(model=gpt4all_path,max_tokens=1000, verbose=True,repeat_last_n=0)
# embeddings = SentenceTransformerEmbeddings(model_name="BAAI/bge-small-en-v1.5")
prompt = PromptTemplate.from_template(template)
llm_chain = LLMChain(prompt=prompt, llm=llm)
combine_docs_chain = create_stuff_documents_chain(llm, prompt)
retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

# Invoke the retrieval chain
response=retrieval_chain.invoke({"input":"What is an appeal?"})

print(response["answer"])
