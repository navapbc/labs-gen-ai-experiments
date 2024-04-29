#!/usr/bin/env python

##
# Use specified LLM to decompose a set of user questions into
# derived/decomposed questions, which will be used to retrieve Guru cards.
# Evaluate the retrieval performance.

# import time
import os
import json
import csv

from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma

import dspy
import dspy_engine

# from retrieval import create_retriever
import ingest
import debugging


@debugging.timer
def load_user_questions():
    # def load_training_json():
    with open("orig_question-guru_cards.json", "r", encoding="utf-8") as data_file:
        json_data = json.load(data_file)
        # print(json.dumps(json_data, indent=2))
        return json_data


@debugging.timer
def load_derived_questions_cache():
    with open("question-transformations.json", "r", encoding="utf-8") as f:
        return json.load(f)


@debugging.timer
def save_derived_questions_cache(indexed_qs):
    qs = list(indexed_qs.values())
    with open("question-transformations.json", "w", encoding="utf-8") as f:
        json.dump(qs, f, indent=2)


def add_transformation(indexed_qs, q_id, q, llm_model, transformation):
    entry = indexed_qs.setdefault(q, {"q_id": q_id, "question": q, "transformations": {}})
    entry["transformations"][llm_model] = transformation


@debugging.timer
def cache_derived_questions(llm_model, predictor):
    qa = load_user_questions()
    qs = load_derived_questions_cache()
    indexed_qs = {item["question"]: item for item in qs}

    for qa_dict in qa:
        question = qa_dict["orig_question"]
        print(qa_dict["id"], question)
        if indexed_qs.get(question).get("transformations").get(llm_model):
            print("  already transformed")
            continue
        try:
            pred = predictor(question=question)
            print("Answer:", pred.answer)
            derived_questions = json.loads(pred.answer)
            if "Answer" in derived_questions:
                # For OpenAI 'gpt-4-turbo' in json mode
                derived_questions = derived_questions["Answer"]
            print("  => ", derived_questions)
            add_transformation(indexed_qs, qa_dict["id"], question, llm_model, derived_questions)
        except Exception as e:
            print("  => Error:", e)
            import traceback

            traceback.print_exc()
            # dspy_engine.print_last_llm_history()
            break

    save_derived_questions_cache(indexed_qs)

    return qs


@debugging.timer
def create_predictor(llm_choice):
    assert llm_choice is not None, "llm_choice must be specified."
    dspy.settings.configure(
        lm=dspy_engine.create_llm_model(llm_choice)  # , rm=create_retriever_model()
    )
    print("LLM model created", dspy.settings.lm)

    system_prompt = 'Decompose into multiple questions so that we can search for relevant SNAP and food assistance eligibility rules. Be concise -- only respond with JSON. Only output the questions as a JSON list: ["question1", "question2", ...]'

    transform_prompt = system_prompt + "The question is: {question}"

    class DecomposeQuestion(dspy.Signature):
        """Decompose into multiple questions so that we can search for relevant SNAP and food assistance eligibility rules. \
Be concise -- only respond with JSON. Only output the questions as a JSON list: ["question1", "question2", ...]. \
The question is: {question}"""

        question = dspy.InputField()
        answer = dspy.OutputField(desc='["question1", "question2", ...]')

    return dspy.Predict(DecomposeQuestion)


def narrow_transformations_to(llm_model, qs):
    return {item["question"]: item["transformations"].get(llm_model) for item in qs}


@debugging.timer
def create_vectordb():
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    return Chroma(
        embedding_function=embeddings,
        # Must use collection_name="langchain" -- https://github.com/langchain-ai/langchain/issues/10864#issuecomment-1730303411
        collection_name="langchain",
        persist_directory="./chroma_db",
    )


def compute_percent_retrieved(retrieved_cards, guru_cards):
    missed_cards = set(guru_cards) - set(retrieved_cards)
    return (len(guru_cards) - len(missed_cards)) / len(guru_cards)


def count_extra_cards(retrieved_cards, guru_cards):
    extra_cards = set(retrieved_cards) - set(guru_cards)
    return len(extra_cards)


@debugging.timer
def eval_retrieval(llm_model, qa, derived_qs, vectordb, retrieve_k=5):
    eval_results = []
    narrowed_qs = narrow_transformations_to(llm_model, derived_qs)
    for qa_dict in qa:
        question = qa_dict["orig_question"]
        guru_cards = qa_dict.get("guru_cards", [])
        # debugging.debug_here(locals())
        if not narrowed_qs[question]:
            print(f"Derived questions not found -- Skipping {question}")
            continue

        questions = narrowed_qs[question]
        results = []
        print(f"Processing user question {qa_dict['id']}: with {len(questions)} derived questions")
        for q in questions:
            retrieval_tups = vectordb.similarity_search_with_relevance_scores(q, k=retrieve_k)
            retrieval = [tup[0] for tup in retrieval_tups]
            retrieved_cards = [doc.metadata["source"] for doc in retrieval]
            scores = [tup[1] for tup in retrieval_tups]
            results.append(
                {
                    "derived_question": q,
                    "retrieved_cards": retrieved_cards,
                    "retrieval_scores": scores,
                    "recall": compute_percent_retrieved(retrieved_cards, guru_cards),
                    "extra_cards": count_extra_cards(retrieved_cards, guru_cards),
                }
            )

        all_retrieved_cards = dict()
        for result in results:
            scores = result["retrieval_scores"]
            for i, card in enumerate(result["retrieved_cards"]):
                all_retrieved_cards[card] = all_retrieved_cards.get(card, 0) + scores[i]

        eval_results.append(
            {
                "id": qa_dict["id"],
                "question": question,
                "derived_questions": questions,
                "results": results,
                "all_retrieved_cards": dict(
                    sorted(
                        all_retrieved_cards.items(),
                        key=lambda item: item[1],
                        reverse=True,
                    )
                ),
                "guru_cards": guru_cards,
                "recall": compute_percent_retrieved(all_retrieved_cards, guru_cards),
                "extra_cards": count_extra_cards(all_retrieved_cards, guru_cards),
            }
        )

    return eval_results


def main0():
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
        ingest.add_json_html_data_to_vector_db(
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

    vectordb = create_vectordb()
    ingest_call(vectordb=vectordb)


def main1():
    llm_model = _llm_model_name
    predictor = create_predictor(llm_model)
    print("Predictor created", predictor)
    cache_derived_questions(llm_model, predictor)


def save_summary_csv(filename, eval_results):
    with open(filename, "w", encoding="utf-8") as file:
        result_fields = ["id", "derived_questions_count", "recall", "extra_cards", "retrieved_cards_count"]
        writer = csv.DictWriter(file, fieldnames=result_fields, extrasaction="ignore")
        writer.writeheader()

        for r in eval_results:
            r["derived_questions_count"] = len(r["derived_questions"])
            r["retrieved_cards_count"] = len(r["all_retrieved_cards"])
            writer.writerow(r)


def main2():
    llm_model = _llm_model_name
    derived_qs = load_derived_questions_cache()

    vectordb = create_vectordb()
    # retriever = create_retriever(vectordb)

    qa = load_user_questions()

    retrieve_k = int(os.environ.get("RETRIEVE_K", "4"))
    eval_results = eval_retrieval(llm_model, qa, derived_qs, vectordb, retrieve_k)

    # timestamp_str = time.strftime('%Y-%m-%d-%H%M%S')
    with open(f"qt-retrieval-eval_results-{llm_model}-k_{retrieve_k}.json", "w", encoding="utf-8") as f:
        json.dump(eval_results, f, indent=4)

    save_summary_csv(f"qt-retrieval-eval_results-{llm_model}-k_{retrieve_k}.csv", eval_results)
    print("\nResult summary:")
    for r in eval_results:
        print(r["id"], r["recall"], r["extra_cards"], len(r["all_retrieved_cards"]))


print("Running...")
_llm_model_name = os.environ.get("LLM_MODEL_NAME", "openhermes")
main2()

# RETRIEVE_K=4 for LLM_MODEL_NAME in mistral:instruct gpt-3.5-turbo gemini-1.0-pro llama3-70b-8192; do echo $LLM_MODEL_NAME; ./decompose-questions.py > "qt-retrieval-eval-$LLM_MODEL_NAME-k_$RETRIEVE_K.log"; echo .; done
