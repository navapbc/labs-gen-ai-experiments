#!/usr/bin/env python

##
# Use specified LLM to decompose a set of user questions into
# derived/decomposed questions, which will be used to retrieve Guru cards.
# Also evaluates the Guru card retrieval performance.

import os
import json
import dotenv

import dspy

# print("Loading our libraries...")
import dspy_engine
import ingest
import debugging

import importlib

dq = importlib.import_module("decompose-questions")

"""
Options
- summarize based on original question vs. derived question vs. both

1. Load original questions
For each original question:
    2. Generate derived questions (from cache if available, otherwise generate and cache)
    3. For each derived question, retrieve Guru cards
    4. Deduplicate Guru cards while retaining associate with corresponding derived questions.
    5. For each Guru card, 
        a. summarize w.r.t. original question (don't need to show)
        b. summarize w.r.t. derived questions (don't show derived questions prominently)

TODO:
- Limit Guru cards based on score and/or card count
- For either or both of the LLM uses, incorporate rationale/CoT (chain-of-thought) to walk the human through the LLM’s thought process so that the user can double-check the LLM’s responses.
- Extract intent of original question and incorporate into derived questions
- Consider adding the glossary Guru card to the vector DB
"""

dotenv.load_dotenv()

# 1. Load original questions
orig_qs = dq.load_user_questions()

# for 2. Generate derived questions (from cache if available, otherwise generate and cache)
# main1_decompose_user_questions
derived_qs = dq.load_derived_questions_cache()
indexed_qs = {item["question"]: item for item in derived_qs}

guru_card_texts = ingest.extract_qa_text_from_guru()

# for 3. For each derived question, retrieve Guru cards
# main2_evaluate_retrieval
vectordb = dq.create_vectordb()
llm_model = os.environ.get("LLM_MODEL_NAME", "openhermes")
print(f"LLM_MODEL_NAME: {llm_model}")
retrieve_k = int(os.environ.get("RETRIEVE_K", "4"))
print("RETRIEVE_K:", retrieve_k)


@debugging.timer
def retrieve_guru_cards_for_question(q_dict, narrowed_qs, vectordb, retrieve_k):
    question = q_dict["orig_question"]
    guru_cards = q_dict.get("guru_cards", [])
    if not narrowed_qs[question]:
        print(f"Derived questions not found -- Skipping {question}")
        return

    questions = narrowed_qs[question]
    results = []
    print(f"Processing user question {q_dict['id']}: with {len(questions)} derived questions")
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
                "recall": dq.compute_percent_retrieved(retrieved_cards, guru_cards),
                "extra_cards": dq.count_extra_cards(retrieved_cards, guru_cards),
            }
        )
    return results


def save_retrieval_results_for_summary():
    narrowed_qs = dq.narrow_transformations_to(llm_model, derived_qs)

    retrieval_results = []
    for question_item in orig_qs:
        derived_qs_retrievals = retrieve_guru_cards_for_question(question_item, narrowed_qs, vectordb, retrieve_k)

        retrieved_card_tallies = {}
        for derived_q_result in derived_qs_retrievals:
            retrieval_scores = derived_q_result["retrieval_scores"]
            for i, card in enumerate(derived_q_result["retrieved_cards"]):
                retrieved_card_tallies[card] = retrieved_card_tallies.get(card, 0) + retrieval_scores[i]

        card_to_dq = {}
        for derived_q_result in derived_qs_retrievals:
            derived_question = derived_q_result["derived_question"]
            for card in derived_q_result["retrieved_cards"]:
                if card not in card_to_dq:
                    card_to_dq[card] = set()
                card_to_dq[card].add(derived_question)

        all_retrieved_cards = {
            card: {"score_sum": tally, "derived_questions": list(card_to_dq[card])}
            for card, tally in retrieved_card_tallies.items()
        }

        exp_guru_cards = question_item.get("guru_cards", [])
        retrieval_results.append(
            {
                "id": question_item["id"],
                "question": question_item["orig_question"],
                "guru_cards": exp_guru_cards,
                "recall": dq.compute_percent_retrieved(all_retrieved_cards, exp_guru_cards),
                "extra_cards": dq.count_extra_cards(all_retrieved_cards, exp_guru_cards),
                "derived_questions": narrowed_qs[question_item["orig_question"]],
                "all_retrieved_cards": dict(
                    sorted(
                        all_retrieved_cards.items(),
                        key=lambda item: item[1]["score_sum"],
                        reverse=True,
                    )
                ),
                # "results": derived_qs_retrievals,
            }
        )

    with open(f"qt_retrieval_results_forSummary-{llm_model}-k_{retrieve_k}.json", "w", encoding="utf-8") as f:
        json.dump(retrieval_results, f, indent=4)


def load_retrieval_results_for_summary():
    with open(f"qt_retrieval_results_forSummary-{llm_model}-k_{retrieve_k}.json", "r", encoding="utf-8") as f:
        return json.load(f)


# 5. For each Guru card,
#     a. summarize w.r.t. original question (don't need to show)
#     b. summarize w.r.t. derived questions (don't show derived questions prominently)


def create_summarizer(llm_choice):
    assert llm_choice is not None, "llm_choice must be specified."
    dspy.settings.configure(
        lm=dspy_engine.create_llm_model(llm_choice)  # , rm=create_retriever_model()
    )
    print("LLM model created", dspy.settings.lm)

    class SummarizeCardGivenQuestion(dspy.Signature):
        """Summarize the following context into 1 sentence without explicitly answering the question(s): {context_question}

        Context: {context}
        """

        context_question = dspy.InputField()
        context = dspy.InputField()
        answer = dspy.OutputField()

    return dspy.Predict(SummarizeCardGivenQuestion)


retrieval_results_for_summary = load_retrieval_results_for_summary()

# 'gemini-1.0-pro' 'gpt-3.5-turbo' 'gpt-3.5-turbo-instruct' 'gpt-4-turbo' 'llama3-70b-8192'
# 'mistral:instruct' 'mixtral-8x7b-32768' 'openhermes'
summarizer_llm_model = "gpt-3.5-turbo-instruct"
summarizer = create_summarizer(summarizer_llm_model)

for rr in retrieval_results_for_summary:
    question = rr["question"]
    retrievals = rr["all_retrieved_cards"]
    print(f"Processing question {rr['id']} with {len(retrievals)} retrieved cards...")
    for i, (card_title, metadata) in enumerate(retrievals.items()):
        score = metadata["score_sum"]
        if i > 3 and score < 0.3:
            continue
        card_text = guru_card_texts[card_title]
        entire_card = "\n".join([card_title, card_text])
        print(f"  {i}. Summarizing {card_title}...")
        derived_questions = " ".join(metadata["derived_questions"] + [question])
        prediction = summarizer(context_question=derived_questions, context=entire_card)
        metadata["entire_card"] = entire_card
        metadata["summary"] = prediction.answer

with open(f"qt_summaries-{summarizer_llm_model}-k_{retrieve_k}.json", "w", encoding="utf-8") as f:
    json.dump(retrieval_results_for_summary, f, indent=4)


# debugging.debug_here(locals())
