#!/usr/bin/env python

##
# Use specified LLM to decompose a set of user questions into
# derived/decomposed questions, which will be used to retrieve Guru cards.
# Also evaluates the Guru card retrieval performance.

import os
import json
import csv
import sys
import traceback
import dotenv

import dataclasses
import dspy

# print("Loading our libraries...")
import dspy_engine
import ingest
import debugging
from decompose_and_summarize import create_predictor, generate_derived_questions, create_vectordb, retrieve_cards, collate_by_card_score_sum


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
            derived_questions = generate_derived_questions(predictor, question)
            add_transformation(indexed_qs, qa_dict["id"], question, llm_model, derived_questions)
        except Exception as e:
            print("  => Error:", e)
            traceback.print_exc()
            # dspy_engine.print_last_llm_history()
            break

    save_derived_questions_cache(indexed_qs)

    return qs


def narrow_transformations_to(llm_model, qs):
    return {item["question"]: item["transformations"].get(llm_model) for item in qs}


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
        if not narrowed_qs[question]:
            print(f"Derived questions not found -- Skipping {question}")
            continue

        questions = narrowed_qs[question]
        print(f"Processing user question {qa_dict['id']}: with {len(questions)} derived questions")
        derived_question_entries = retrieve_cards(questions, vectordb, retrieve_k)
        results = []
        for r in derived_question_entries:
            results.append(
                {
                    "derived_question": r.derived_question,
                    "retrieved_cards": r.retrieved_cards,
                    "retrieval_scores": r.retrieval_scores,
                    "recall": compute_percent_retrieved(r.retrieved_cards, guru_cards),
                    "extra_cards": count_extra_cards(r.retrieved_cards, guru_cards),
                }
            )

        sorted_cards_dict = dict([(entry.card,entry.score_sum) for entry in collate_by_card_score_sum(derived_question_entries)])
        sorted_cards = list(sorted_cards_dict)

        eval_results.append(
            {
                "id": qa_dict["id"],
                "question": question,
                "derived_questions": questions,
                "results": results,
                "all_retrieved_cards": sorted_cards_dict,
                "guru_cards": guru_cards,
                "recall": compute_percent_retrieved(sorted_cards, guru_cards),
                "extra_cards": count_extra_cards(sorted_cards, guru_cards),
            }
        )

    return eval_results


def main0_ingest_guru_cards():
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
    # Use smaller chunks for shorter-length quotes
    ingest_call(vectordb=vectordb, chunk_size=250, chunk_overlap=100)


def main1_decompose_user_questions():
    llm_model = os.environ.get("LLM_MODEL_NAME", "openhermes")
    print(f"LLM_MODEL_NAME: {llm_model}")
    predictor = create_predictor(llm_model)
    print("Predictor created", predictor)
    cache_derived_questions(llm_model, predictor)


def main2_evaluate_retrieval():
    derived_qs = load_derived_questions_cache()
    list_models(derived_qs)
    vectordb = create_vectordb()
    qa = load_user_questions()

    llm_model = os.environ.get("LLM_MODEL_NAME", "openhermes")
    print(f"LLM_MODEL_NAME: {llm_model}")
    retrieve_k = int(os.environ.get("RETRIEVE_K", "4"))
    print("RETRIEVE_K:", retrieve_k)
    eval_results = eval_retrieval(llm_model, qa, derived_qs, vectordb, retrieve_k)

    with open(f"qt-retrieval-eval_results-{llm_model}-k_{retrieve_k}.json", "w", encoding="utf-8") as f:
        json.dump(eval_results, f, indent=4)

    save_summary_csv(f"qt-retrieval-eval_results-{llm_model}-k_{retrieve_k}.csv", eval_results)
    print("\nResult summary: (id, recall, extra_cards, retrieved_cards_count)")
    for r in eval_results:
        print(r["id"], r["recall"], r["extra_cards"], len(r["all_retrieved_cards"]))


def save_summary_csv(filename, eval_results):
    with open(filename, "w", encoding="utf-8") as file:
        result_fields = ["id", "derived_questions_count", "recall", "extra_cards", "retrieved_cards_count"]
        writer = csv.DictWriter(file, fieldnames=result_fields, extrasaction="ignore")
        writer.writeheader()

        for r in eval_results:
            r["derived_questions_count"] = len(r["derived_questions"])
            r["retrieved_cards_count"] = len(r["all_retrieved_cards"])
            writer.writerow(r)


def list_models(derived_qs):
    models = set()
    for item in derived_qs:
        models.update(item["transformations"].keys())
    cached_models = sorted(models)
    print("Available LLM models in derived questions cache:", " ".join(f"'{m}'" for m in cached_models))
    return cached_models


if __name__ == "__main__":
    print("""
    0. ingest Guru cards into vector DB
    1. cache decomposed/derived questions
    2. evaluate Guru card retrieval""")
    dotenv.load_dotenv()
    if args := sys.argv[1:]:
        choice = args[0]
        print("Running option:", choice)
    else:
        print("What would you like to do?")
        choice = input()

    if choice in ["0", "ingest"]:
        main0_ingest_guru_cards()
    elif choice in ["1", "decompose"]:
        main1_decompose_user_questions()
    elif choice in ["2", "evaluate"]:
        main2_evaluate_retrieval()

# Copy and paste to evaluate several models on the command line:
# RETRIEVE_K=4 for LLM_MODEL_NAME in mistral:instruct ...; do ./decompose-questions.py evaluate > "qt-retrieval-eval-$LLM_MODEL_NAME-k_$RETRIEVE_K.log"; echo .; done
