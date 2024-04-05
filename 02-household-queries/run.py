import os
import json
import dotenv
from langchain_community.embeddings import (
    SentenceTransformerEmbeddings,
    HuggingFaceEmbeddings,
)
from langchain_community.llms import GPT4All
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from ingest import ingest_call
from retrieval import create_retriever, retrieval_call
from llm import ollama_client

dotenv.load_dotenv()

_embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")
_llm_model_name = os.environ.get("LLM_MODEL_NAME", "mistral")

print(f"""
Which embedding function would you like to use?
1. Google Gen AI (default)
2. all-MiniLM-L6-v2
3. $EMBEDDINGS_MODEL_NAME ({_embeddings_model_name}) via HuggingFace
      """)
embedding_choice = input()
# Set embedding function
if embedding_choice == "2" or embedding_choice == "all-MiniLM-L6-v2":
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
elif embedding_choice == "3":
    # "The all-mpnet-base-v2 model provides the best quality, while all-MiniLM-L6-v2 is 5 times faster and still offers good quality."
    embeddings = HuggingFaceEmbeddings(model_name=_embeddings_model_name)
else:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

print(f"""
Which LLM would you like to use? 
1. Gemini (default)
2. Mistral (via GPT4All)
3. $LLM_MODEL_NAME ({_llm_model_name}) via Ollama
      """)

llm_choice = input()
# Load the models
if llm_choice == "2" or llm_choice == "Mistral":
    # Open source option
    # download Mistral at https://mistral.ai/news/announcing-mistral-7b/
    gpt4all_path = "./mistral-7b-instruct-v0.1.Q4_0.gguf"
    llm = GPT4All(model=gpt4all_path, max_tokens=1000, verbose=True, repeat_last_n=0)
elif llm_choice == "3":
    # _llm_model_name = "mistral" # "openhermes", "llama2", "mistral"
    llm_settings = {"temperature": 0.1}
    llm = ollama_client(_llm_model_name, settings=llm_settings)
else:
    # Get a Google API key by following the steps after clicking on Get an API key button
    # at https://ai.google.dev/tutorials/setup
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        verbose=True,
        google_api_key=GOOGLE_API_KEY,
        convert_system_message_to_human=True,
    )

# initialize chroma db
vectordb = Chroma(
    embedding_function=embeddings,
    collection_name="resources",
    persist_directory="./chroma_db",
)


def load_training_json():
    with open("question_answer_citations.json", encoding="utf-8") as data_file:
        json_data = json.load(data_file)
        # print(json.dumps(json_data, indent=2))
        return json_data


def evaluate_retrieval():
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
        results.append(
            {
                "id": qa_dict["id"],
                "question": question,
                "guru_cards": guru_cards,
                "retrieved_cards": [doc.metadata["source"] for doc in retrieval],
            }
        )
    print(retriever)
    print(
        "EVALUATION RESULTS:\n", "\n".join([json.dumps(r, indent=2) for r in results])
    )


print("""
Initialize DB and retrieve? 
1. Retrieve only (default)
2. Ingest and retrieve
3. Ingest only
4. Evaluate retrieval
      """)
run_option = input()
if run_option == "2":
    ingest_call(vectordb=vectordb)
    retrieval_call(llm=llm, vectordb=vectordb)
elif run_option == "3":
    ingest_call(vectordb=vectordb)
elif run_option == "4":
    evaluate_retrieval()
else:
    retrieval_call(llm=llm, vectordb=vectordb)
