from bs4 import BeautifulSoup
import os
import dotenv
import json
from langchain_community.document_loaders import PDFMinerLoader
from langchain.docstore.document import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    NLTKTextSplitter,
    SpacyTextSplitter,
)

from langchain_community.embeddings import (
    SentenceTransformerEmbeddings,
    HuggingFaceEmbeddings,
)
# from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from llm import ollama_client


dotenv.load_dotenv()

# _llm_model_name = os.environ.get("LLM_MODEL_NAME", "mistral")

# llm = ollama_client(_llm_model_name, settings={"temperature": 0.1})


EMBEDDINGS = {
    "all-MiniLM-L6-v2": {
        "func": SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2"),
        "token_limit": 256,
    },
    "HuggingFace::all-MiniLM-L6-v2": {
        "func": HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"),
        "token_limit": 256,
    },
    # "Google::models/embedding-001": {
    #     "func": GoogleGenerativeAIEmbeddings(model="models/embedding-001"),
    #     "token_limit": 2048,
    # },
    # "google_models/text-embedding-004": {
    #     "func": GoogleGenerativeAIEmbeddings(model="models/text-embedding-004"),
    #     "token_limit": 768,
    # },
    "BAAI/bge-small-en-v1.5": {
        "func": SentenceTransformerEmbeddings(model_name="BAAI/bge-small-en-v1.5"),
        "token_limit": 512,
    },
    "mixedbread-ai/mxbai-embed-large-v1": {
        "func": SentenceTransformerEmbeddings(model_name="mixedbread-ai/mxbai-embed-large-v1"),
        "token_limit": 1024,
    },
}


# split text into chunks
def get_text_chunks_langchain(text, source, chunk_size, chunk_overlap, token_limit, text_splitter_choice, silent):
    if text_splitter_choice == "2":
        text_splitter = NLTKTextSplitter()
    elif text_splitter_choice == "3":
        text_splitter = SpacyTextSplitter()
    else:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    entire_text = source + "\n\n" + text
    texts = text_splitter.split_text(entire_text)

    if not silent:
        print("  Split into", len(texts))
    for t in texts:
        token_count = llm.get_num_tokens(t)
        if token_count > token_limit:
            print(f"Exceeded token limit of {token_limit}: {token_count};")

    docs = [
        Document(
            page_content=t,
            metadata={"source": source.strip(), "entire_card": entire_text},
        )
        for t in texts
    ]

    return docs


# Chunk the pdf and load into vector db
def add_pdf_to_vector_db(vectordb, file_path, embedding_name=None, chunk_size=500, chunk_overlap=100):
    if embedding_name:
        check_embedding(chunk_size, EMBEDDINGS.get(embedding_name, ""))
    # PDFMinerLoader only gives metadata when extract_images=True due to default using lazy_loader
    loader = PDFMinerLoader(file_path, extract_images=True)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    pdf_pages = loader.load_and_split(text_splitter)
    print("Loading PDF chunks into vector db")
    vectordb.add_documents(documents=pdf_pages)


# Chunk the json data and load into vector db
def add_json_html_data_to_vector_db(
    vectordb,
    file_path,
    content_key,
    index_key,
    token_limit,
    embedding_name=None,
    text_splitter_choice=1,
    chunk_size=750,
    chunk_overlap=300,
    silent=False,
):
    data_file = open(file_path, encoding="utf-8")
    json_data = json.load(data_file)
    if embedding_name:
        check_embedding(chunk_size, EMBEDDINGS.get(embedding_name, ""))
    for content in json_data:
        if not content[index_key].strip().endswith("?"):
            continue
        soup = BeautifulSoup(content[content_key], "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        if not silent:
            print("Processing document:", content[index_key])
        chunks = get_text_chunks_langchain(
            text,
            content[index_key],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            token_limit=token_limit,
            text_splitter_choice=text_splitter_choice,
            silent=silent,
        )
        vectordb.add_documents(documents=chunks)


def ingest_call(
    vectordb,
    embedding_name=None,
    text_splitter_choice=1,
    chunk_size=750,
    chunk_overlap=300,
    token_limit=256,
    silent=False,
):
    # download from https://drive.google.com/drive/folders/1DkAQ03bBVIPoO1d8gcHVnilQ-9VXfhJ8?usp=drive_link
    guru_file_path = "./guru_cards_for_nava.json"
    add_json_html_data_to_vector_db(
        vectordb=vectordb,
        file_path=guru_file_path,
        embedding_name=embedding_name,
        content_key="content",
        index_key="preferredPhrase",
        silent=silent,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        token_limit=token_limit,
        text_splitter_choice=text_splitter_choice,
    )


def check_embedding(chunk_size, embedding):
    token_limit = embedding.get("token_limit", 0)
    if token_limit != 0 and chunk_size > token_limit:
        print(f"You've defined the chunk size as {chunk_size}, the token limit for this embedding is {token_limit}")
