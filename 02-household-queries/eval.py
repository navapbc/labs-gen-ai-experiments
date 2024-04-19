import json
import csv
import itertools
from datetime import datetime
import os

from langchain_community.llms.ollama import Ollama
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

from tqdm import tqdm
from openai import OpenAI
import cohere

import chromadb
from chromadb.config import Settings

from ingest import ingest_call

################################################################
# Prompts
################################################################

PROMPT = """You are helping a client with their application to SNAP (food stamps).
Please concisely and politely answer the following question from the client.
Question: {question_text}"""

PROMPT_WITH_CONTEXT = """You are helping a client with their application to SNAP (food stamps).
Please concisely and politely answer the following question from the client.
Question: {question_text}

Please answer using the following context:
{context}"""

HYDE_PROMPT = """Please write a hypothetical document that would answer the following question about SNAP (food stamps.)
The document should start by repeating the question in more generic format and then provide the answer.
The resulting Q&A should be in the style of a document that a caseworker would use to answer an applicant's question.
In total, the document should be about 200 words long.
Do not include disclaimers about "consulting with a SNAP eligiblity worker", etc.
Question: {question_text}"""

# From Phoenix Evals ("HUMAN_VS_AI_PROMPT_TEMPLATE")
EVAL_PROMPT = """You are comparing a human ground truth answer from an expert to an answer from an AI model.
Your goal is to determine if the AI answer correctly matches, in substance, the human answer.
    [BEGIN DATA]
    ************
    [Question]: {question_text}
    ************
    [Human Ground Truth Answer]: {correct_answer}
    ************
    [AI Answer]: {ai_generated_answer}
    ************
    [END DATA]
Compare the AI answer to the human ground truth answer, if the AI correctly answers the question,
then the AI answer is "correct". If the AI answer is longer but contains the main idea of the
Human answer please answer "correct". If the AI answer divergences or does not contain the main
idea of the human answer, please answer "incorrect"."""

################################################################
# LLM Wrappers
################################################################

mistral_7b_client = None


def mistral_7b(prompt):
    global mistral_7b_client
    if not mistral_7b_client:
        mistral_7b_client = Ollama(model="mistral")
    return mistral_7b_client.invoke(prompt)


openai_client = None


def gpt3_5(prompt, model="gpt-3.5-turbo"):
    global openai_client
    if not openai_client:
        openai_client = OpenAI()  # Uses OPENAI_API_KEY
    return (
        openai_client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}]
        )
        .choices[0]
        .message.content
    )


def gpt_4_turbo(prompt):
    return gpt3_5(prompt, model="gpt-4-turbo")


################################################################
# Evaluation set up
################################################################

parameters = {
    # (size, overlap)
    "chunk_size": [(256, 0)],
    "k": [5],
    "reranking": [False],
    "hyde": [False],
    "model": [mistral_7b],  # [gpt_4_turbo],
}

eval_llm_client = mistral_7b  # gpt_4_turbo

with open("question_answer_citations.json", "r") as file:
    questions = json.load(file)

# Generate all possible combinations of parameters
parameter_names, values = zip(*parameters.items())
parameter_permutations = list(itertools.product(*values))

################################################################
# Generating answers for a given question + set of parameters
################################################################

# We'll call this function for each question in the Q&A set,
# so we don't want to re-ingest all the data for each question
vector_db_client = chromadb.PersistentClient(
    settings=Settings(allow_reset=True), path="./chroma_db"
)
vector_db = None
vector_db_chunk_size = None


def get_answer(question, parameters):
    global vector_db_chunk_size, vector_db

    # No retrieval?
    if parameters["k"] == 0:
        return parameters["model"](PROMPT.format(question_text=question))

    # If chunk size/overlap changed, re-ingest the data
    if vector_db_chunk_size != parameters["chunk_size"]:
        chunk_size, chunk_overlap = parameters["chunk_size"]

        vector_db_client.reset()
        # Rebuild whatever this is to avoid chromadb.errors.InvalidCollectionException
        vector_db = Chroma(
            client=vector_db_client,
            collection_name="resources",
            persist_directory="./chroma_db",
            embedding_function=SentenceTransformerEmbeddings(
                model_name="all-MiniLM-L6-v2"
            ),
        )

        ingest_call(
            vector_db, silent=True, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        vector_db_chunk_size = parameters["chunk_size"]

    context_search = (
        hyde(parameters["model"], question) if parameters["hyde"] else question
    )

    docs = vector_db.similarity_search(context_search, k=parameters["k"])
    unique_cards = set(doc.metadata["entire_card"] for doc in docs)
    reranked_cards = (
        rerank(question, unique_cards) if parameters["reranking"] else unique_cards
    )
    context = "\n".join(reranked_cards)

    return parameters["model"](
        PROMPT_WITH_CONTEXT.format(question_text=question, context=context)
    )


cohere_client = None


def rerank(question, docs):
    global cohere_client
    if not cohere_client:
        cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))
    results = cohere_client.rerank(
        query=question,
        documents=docs,
        top_n=3,
        model="rerank-english-v2.0",
        return_documents=True,
    )
    return [r.document.text for r in results.results]


def hyde(model, question):
    return model(HYDE_PROMPT.format(question_text=question))


################################################################
# Iterating through each question for a given set of parameters
################################################################


def evaluate(eval_llm_client, questions, parameters):
    results = []
    for question in tqdm(questions, leave=False, desc="Evaluating questions"):
        result = {
            "question_id": question["id"],
            "question_text": question["question"],
            "correct_answer": question[
                "orig_answer" if not "short_answer" in question else "answer"
            ],
            "ai_generated_answer": get_answer(question["question"], parameters),
        }
        result["evaluation"] = eval_llm_client(EVAL_PROMPT.format(**result))
        result["correct"] = not "incorrect" in result["evaluation"].lower()
        result |= parameters
        result["model"] = result["model"].__name__
        results.append(result)
    return results


################################################################
# Iterating through every combination of parameters
################################################################

evaluation_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
with open(f"evaluation_results_{evaluation_timestamp}.csv", "w") as file:
    result_keys = (
        ["question_id"]
        + list(parameters.keys())
        + [
            "question_text",
            "correct_answer",
            "ai_generated_answer",
            "evaluation",
            "correct",
        ]
    )
    writer = csv.DictWriter(file, fieldnames=result_keys)
    writer.writeheader()

    for i, parameter_values in enumerate(
        tqdm(parameter_permutations, desc="Evaluating parameter combinations")
    ):
        param_dict = dict(zip(parameter_names, parameter_values))
        results = evaluate(eval_llm_client, questions, param_dict)
        writer.writerows(results)
