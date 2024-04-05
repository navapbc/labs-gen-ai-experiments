from bs4 import BeautifulSoup
from langchain_community.document_loaders import PDFMinerLoader
from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json


# split text into chunks
def get_text_chunks_langchain(text, source):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=500)
    texts = text_splitter.split_text(text)
    docs = [Document(page_content=t, metadata={"source": source}) for t in texts]
    return docs


# Chunk the pdf and load into vector db
def add_pdf_to_vector_db(vectordb, file_path, chunk_size=500, chunk_overlap=100):
    # PDFMinerLoader only gives metadata when extract_images=True due to default using lazy_loader
    loader = PDFMinerLoader(file_path, extract_images=True)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    pdf_pages = loader.load_and_split(text_splitter)
    print("Loading PDF chunks into vector db")
    vectordb.add_documents(documents=pdf_pages)


# Chunk the json data and load into vector db
def add_json_html_data_to_vector_db(vectordb, file_path, content_key, index_key):
    data_file = open(file_path, encoding="utf-8")
    json_data = json.load(data_file)

    for content in json_data:
        soup = BeautifulSoup(content[content_key], "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        chunks = get_text_chunks_langchain(text, content[index_key])
        print(f"Loading Document {content[index_key]} chunk into vector db")
        vectordb.add_documents(documents=chunks)


def ingest_call(vectordb):
    # Load the PDF and create chunks
    # download from https://drive.google.com/file/d/1--qDjraIk1WGxwuCGBP-nfxzOr9IHvcZ/view?usp=drive_link
    pdf_path = "./tanf.pdf"
    add_pdf_to_vector_db(vectordb=vectordb, file_path=pdf_path)

    # download from https://drive.google.com/drive/folders/1DkAQ03bBVIPoO1d8gcHVnilQ-9VXfhJ8?usp=drive_link
    guru_file_path = "./guru_cards_for_nava.json"
    add_json_html_data_to_vector_db(
        vectordb=vectordb,
        file_path=guru_file_path,
        content_key="content",
        index_key="preferredPhrase",
    )
