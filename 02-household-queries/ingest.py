from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_community.llms import GPT4All
from bs4 import BeautifulSoup
from langchain_community.document_loaders import JSONLoader, PDFMinerLoader
from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain, LLMChain, RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
import json
import os
from pathlib import Path
from pprint import pprint
import dotenv

dotenv.load_dotenv()

# Load the models
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
llm = ChatGoogleGenerativeAI(model="gemini-pro",
                             verbose = True,google_api_key=GOOGLE_API_KEY,
                             convert_system_message_to_human=True)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# initialize chroma db
vectordb=Chroma(embedding_function=embeddings, collection_name="resources")
# Load the PDF and create chunks
# download from https://drive.google.com/file/d/1--qDjraIk1WGxwuCGBP-nfxzOr9IHvcZ/view?usp=drive_link

pdf_path = "./tanf.pdf"
# PDFMinerLoader only gives metadata when extract_images=True due to default using lazy_loader
loader = PDFMinerLoader(pdf_path, extract_images=True)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

pdf_pages = loader.load_and_split(text_splitter)
vectordb.add_documents(documents=pdf_pages)

# Load the json and create chunks
# download from https://drive.google.com/file/d/1UoWmktXS5nqgIWj2x_O5hgzwU0yVuaJc/view
guru_file_path='./guru_cards_for_nava.json'

def get_text_chunks_langchain(text, source):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=500)
    texts = text_splitter.split_text(text)
    docs = [Document(page_content=t, metadata={"source":source}) for t in texts]
    return docs

guru_data_file = open(guru_file_path)
guru_data = json.load(guru_data_file)

for content in guru_data:
    soup = BeautifulSoup(content["content"], "html.parser")
    text = soup.get_text(separator='\n', strip=True)
    chunks = get_text_chunks_langchain(text, content["preferredPhrase"])
    vectordb.add_documents(documents=chunks)


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
retrieval_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
    verbose=False,
)

# Invoke the retrieval chain
response=retrieval_chain.invoke({"query":"Should all household members be listed even if they are not in the food stamp household?"})
print("RESULT: ", response["result"])
print("SOURCE DOC: ",response["source_documents"])