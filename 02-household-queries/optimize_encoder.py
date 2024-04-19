import os
from bs4 import BeautifulSoup
import dotenv
from langchain.docstore.document import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    NLTKTextSplitter,
    SpacyTextSplitter,
)
import json
from langchain_community.embeddings import (
    SentenceTransformerEmbeddings,
    HuggingFaceEmbeddings,
)
import chromadb
from chromadb.config import Settings
from llm import ollama_client
# from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from retrieval import create_retriever
from langchain_community.vectorstores import Chroma
import nltk
import spacy

dotenv.load_dotenv()

_llm_model_name = os.environ.get("LLM_MODEL_NAME", "mistral")

llm = ollama_client(_llm_model_name, settings={"temperature": 0.1})

EMBEDDINGS = {
    "st_all-MiniLM-L6-v2": {
        "func": SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2"),
        "token_limit": 256,
    },
    "hf_all-MiniLM-L6-v2": {
        "func": HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"),
        "token_limit": 256,
    },
    #  "google_models/embedding-001": {"func": GoogleGenerativeAIEmbeddings(model="models/embedding-001"), "token_limit":2048},
    #  "google_models/text-embedding-004": {"func": GoogleGenerativeAIEmbeddings(model="models/text-embedding-004"), "token_limit":768},
    "BAAI/bge-small-en-v1.5": {
        "func": SentenceTransformerEmbeddings(model_name="BAAI/bge-small-en-v1.5"),
        "token_limit": 512,
    },
    "mixedbread-ai/mxbai-embed-large-v1": {
        "func": SentenceTransformerEmbeddings(
            model_name="mixedbread-ai/mxbai-embed-large-v1"
        ),
        "token_limit": 1024,
    },
}


def load_training_json():
    with open("question_answer_citations.json", encoding="utf-8") as data_file:
        json_data = json.load(data_file)
        # print(json.dumps(json_data, indent=2))
        return json_data


def compute_percent_retrieved(retrieved_cards, guru_cards):
    missed_cards = set(guru_cards) - set(retrieved_cards)
    return (len(guru_cards) - len(missed_cards)) / len(guru_cards)


def count_extra_cards(retrieved_cards, guru_cards):
    extra_cards = set(retrieved_cards) - set(guru_cards)
    return len(extra_cards)


# split text into chunks
def get_text_chunks_langchain(
    text, source, chunk_size, chunk_overlap, token_limit, text_splitter_choice
):
    if text_splitter_choice == "2":
        text_splitter = NLTKTextSplitter()
    elif text_splitter_choice == "3":
        text_splitter = SpacyTextSplitter()
    else:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    texts = text_splitter.split_text(source + "\n\n" + text)
    # print("  Split into", len(texts))
    for t in texts:
        token_count = llm.get_num_tokens(t)
        overlap_and_token = token_count + chunk_overlap
        if token_count > token_limit:
            print(f"Exceeded token limit of {token_limit}: {token_count}; {t}")
        elif chunk_size > (overlap_and_token):
            print(f"Exceeded token count and overlap {overlap_and_token}: {chunk_size}; {t}" )

    docs = [
        Document(page_content=t, metadata={"source": source.strip()}) for t in texts
    ]

    return docs


# Chunk the json data and load into vector db
def add_json_html_data_to_vector_db(
    vectordb,
    file_path,
    content_key,
    index_key,
    chunk_size,
    chunk_overlap,
    token_limit,
    text_splitter_choice,
):
    data_file = open(file_path, encoding="utf-8")
    json_data = json.load(data_file)
    for content in json_data:
        if not content[index_key].strip().endswith("?"):
            continue
        soup = BeautifulSoup(content[content_key], "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        # print("Processing document:", content[index_key])
        chunks = get_text_chunks_langchain(
            text,
            content[index_key],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            token_limit=token_limit,
            text_splitter_choice=text_splitter_choice,
        )
        vectordb.add_documents(documents=chunks)


def ingest_call(vectordb, chunk_size, chunk_overlap, token_limit, text_splitter_choice):
    # download from https://drive.google.com/drive/folders/1DkAQ03bBVIPoO1d8gcHVnilQ-9VXfhJ8?usp=drive_link
    guru_file_path = "./guru_cards_for_nava.json"
    add_json_html_data_to_vector_db(
        vectordb=vectordb,
        file_path=guru_file_path,
        content_key="content",
        index_key="preferredPhrase",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        token_limit=token_limit,
        text_splitter_choice=text_splitter_choice,
    )


def evaluate_retrieval(vectordb):
    qa = load_training_json()
    results = []
    retriever = create_retriever(vectordb)
    for qa_dict in qa[1:]:
        orig_question = qa_dict["orig_question"]
        question = qa_dict.get("question", orig_question)
        # print(f"\nQUESTION {qa_dict['id']}: {question}")
        guru_cards = qa_dict.get("guru_cards", [])
        # print(f"  Desired CARDS : {guru_cards}")

        retrieval = retriever.invoke(question)
        retrieved_cards = [doc.metadata["source"] for doc in retrieval]
        results.append(
            {
                "id": qa_dict["id"],
                "question": question,
                "guru_cards": guru_cards,
                "retrieved_cards": retrieved_cards,
                "recall": compute_percent_retrieved(retrieved_cards, guru_cards),
                "extra_cards": count_extra_cards(retrieved_cards, guru_cards),
            }
        )
    recall_results = print_and_set_recall_stats(results)
    return recall_results


def print_and_set_recall_stats(results):
    recall_results = {}
    recall = 0
    extra_card_count = 0

    print("\nTable:")
    for res in results:
        print(res["id"], "|", res["recall"], "|", res["extra_cards"])
        extra_card_count += res["extra_cards"]
        recall += res["recall"]
    recall_results["result"] = results
    recall_results["recall_percentage"] = recall / len(results)
    recall_results["extra_card_count"] = extra_card_count
    return recall_results


def run_embedding_func_and_eval_retrieval(
    embeddings, chunk_size, chunk_overlap, text_splitter_choice
):
    selected_embedding = embeddings["func"]
    persistent_client = chromadb.PersistentClient(
        settings=Settings(allow_reset=True), path="./chroma_db"
    )

    vectordb = Chroma(
        client=persistent_client,
        collection_name="resources",
        persist_directory="./chroma_db",
        embedding_function=selected_embedding,
    )
    ingest_call(
        vectordb=vectordb,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        token_limit=embeddings["token_limit"],
        text_splitter_choice=text_splitter_choice,
    )
    recall_results = evaluate_retrieval(vectordb)
    persistent_client.reset()
    return recall_results


print("""
      Choose a text splitter
      1. RecursiveCharacterTextSplitter(Default)
      2. NLTK
      3. Spacy
      """)

text_splitter_choice = input()
chunk_size = 750
chunk_overlap = 300
if text_splitter_choice == "2":
    nltk.download("punkt")
elif text_splitter_choice == "3":
    spacy.cli.download("en_core_web_sm")
else:
    print("Define chunk size: 750(default) ")
    chunk_size = int(input())
    print("Define chunk overlap: 300(default) ")
    chunk_overlap = int(input())

chunk_size = 750 if chunk_size is None else chunk_size
chunk_overlap = 300 if chunk_overlap is None else chunk_overlap

overall_results = []
for embedding in EMBEDDINGS:
    print("Embedding: " + embedding)
    results = run_embedding_func_and_eval_retrieval(
        EMBEDDINGS[embedding],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        text_splitter_choice=text_splitter_choice,
    )
    results["embedding_name"] = embedding
    overall_results.append(results)

max_recall = max(overall_results, key=lambda x: x["recall_percentage"])
print(max_recall["embedding_name"], max_recall["recall_percentage"])