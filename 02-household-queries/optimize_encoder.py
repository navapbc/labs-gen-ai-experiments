import json
import dotenv
from langchain.docstore.document import Document
import chromadb
from chromadb.config import Settings
from dspy_engine import load_training_json
from ingest import EMBEDDINGS, ingest_call
from retrieval import create_retriever
from langchain_community.vectorstores import Chroma
import nltk
import spacy

dotenv.load_dotenv()


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
    embedding_name, embeddings, chunk_size, chunk_overlap, text_splitter_choice
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
        embedding_name=embedding_name,
        token_limit=embeddings["token_limit"],
        text_splitter_choice=text_splitter_choice,
        silent=True,
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
    chunk_size = int(input() or 750)
    print("Define chunk overlap: 300(default) ")
    chunk_overlap = int(input() or 300)

chunk_size = 750 if chunk_size is None else chunk_size
chunk_overlap = 300 if chunk_overlap is None else chunk_overlap

overall_results = []
for embedding in EMBEDDINGS:
    print("Embedding: " + embedding)
    results = run_embedding_func_and_eval_retrieval(
        embedding,
        EMBEDDINGS[embedding],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        text_splitter_choice=text_splitter_choice,
    )
    results["embedding_name"] = embedding
    overall_results.append(results)

max_recall = max(overall_results, key=lambda x: x["recall_percentage"])
print(max_recall["embedding_name"], max_recall["recall_percentage"])
