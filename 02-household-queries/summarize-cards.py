#!/usr/bin/env python

##
# Use specified LLM to decompose a set of user questions into
# derived/decomposed questions, which will be used to retrieve Guru cards.
# Also evaluates the Guru card retrieval performance.

import sys
import os
import json
import importlib
import dotenv

import dspy

# print("Loading our libraries...")
import dspy_engine
import ingest
import debugging

dq = importlib.import_module("decompose-questions")

"""
Overall process:
1. Load original questions
For each original question:
    2. Load derived questions from cache
    3. For each derived question, retrieve Guru cards
    4. Deduplicate Guru cards while retaining associate with corresponding derived questions.
    5. For each Guru card, summarize w.r.t. original question and derived questions

Parameters:
- Question-Transformer LLM and its prompt
- Retrieval k
- Summarizer LLM and its prompt

Next steps:
- improve recall
  - increase k ("using a bigger net"), which will result in more retrieved (likely irrelevant) cards
  - improve derived questions via prompt engineering; but currently specific to Household questions
  - postpone until we have Multi-benefit questions
  - use manually-rephrased questions and move on focus on summaries
- improve summaries, assuming/forcing retrieved cards to be relevant
  - work on providing quotes
  - incorporate rationale/CoT (chain-of-thought)

Goals?
- Optimize software given dataset (recall, accuracy, etc.)
- Build capabilities (summarizing, quoting, rationale/CoT, etc.)


TODO:
- Update LLM prompts based on summary comments in PR
- For either or both of the LLM uses, incorporate rationale/CoT (chain-of-thought) to walk the human through the LLM's thought process so that the user can double-check the LLM’s responses.
- Extract intent of original question and incorporate into derived questions
- Print a 1-2 sentence quote from the card
- Consider adding the glossary Guru card to the vector DB
"""


@debugging.timer
def retrieve_guru_cards_for_question(q_dict, narrowed_qs, vectordb, retrieve_k):
    question = q_dict["orig_question"]
    guru_cards = q_dict.get("guru_cards", [])
    if not narrowed_qs[question]:
        print(f"Derived questions not found -- Skipping {question}")
        return None

    derived_questions = narrowed_qs[question]
    results = []
    print(f"Processing user question {q_dict['id']}: with {len(derived_questions)} derived questions")
    for q in derived_questions:
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


def get_retrieval_results(orig_qs, narrowed_qs, vectordb, retrieve_k):
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
    return retrieval_results


def create_summarizer():
    class SummarizeCardGivenQuestion(dspy.Signature):
        """Summarize the following context into 1 sentence without explicitly answering the question(s): {context_question}

        Context: {context}
        """

        context_question = dspy.InputField()
        context = dspy.InputField()
        answer = dspy.OutputField()

    return dspy.Predict(SummarizeCardGivenQuestion)


def create_summaries(retrieval_results, summarizer_llm_model, guru_card_texts):
    assert summarizer_llm_model is not None, "summarizer_llm_model must be specified."
    llm = dspy_engine.create_llm_model(summarizer_llm_model)  # , rm=create_retriever_model()
    print("LLM model created", llm)

    summarizer = create_summarizer()
    for rr in retrieval_results:
        retrievals = rr["all_retrieved_cards"]
        print(f"Processing question {rr['id']} with {len(retrievals)} retrieved cards...")
        for i, (card_title, metadata) in enumerate(retrievals.items()):
            # Limit summarizing of Guru cards based on score and card count
            if i > 3 and metadata["score_sum"] < 0.3:
                continue
            card_text = guru_card_texts[card_title]
            entire_card = "\n".join([card_title, card_text])
            # Summarize based on derived question and original question
            # Using only the original question causes the LLM to try to answer the question.
            context_questions = " ".join(metadata["derived_questions"] + [rr["question"]])
            with dspy.context(lm=llm):
                print(f"  {i}. Summarizing {card_title}...")
                prediction = summarizer(context_question=context_questions, context=entire_card)
            metadata["entire_card"] = entire_card
            metadata["summary"] = prediction.answer

    # retrieval_results are updated with summaries
    return retrieval_results


def main(cmd_choice):
    # LLM Options: 'gemini-1.0-pro' 'gpt-3.5-turbo' 'gpt-3.5-turbo-instruct' 'gpt-4-turbo'
    #   'llama3-70b-8192' 'mistral:instruct' 'mixtral-8x7b-32768' 'openhermes'
    questioner_llm_model = os.environ.get("LLM_MODEL_NAME", "openhermes")
    print(f"Questioner LLM_MODEL_NAME: {questioner_llm_model}")
    retrieve_k = int(os.environ.get("RETRIEVE_K", "4"))
    print("RETRIEVE_K:", retrieve_k)
    filename_prefix = f"qt-{questioner_llm_model}-k_{retrieve_k}"
    retrieval_results_filename = f"{filename_prefix}--retrievals.json"

    if cmd_choice in ["1", "save_retrieval_results"]:
        # Load original questions verbatim from BDT
        orig_qs = dq.load_user_questions()

        # Load derived questions from cache to minimize LLM cost
        # To create the cache, run decompose-questions.py's main1_decompose_user_questions()
        derived_qs = dq.load_derived_questions_cache()

        # Set up Guru card retrieval for each derived question
        # Similar to decompose-questions.py's main2_evaluate_retrieval
        vectordb = dq.create_vectordb()

        narrowed_qs = dq.narrow_transformations_to(questioner_llm_model, derived_qs)

        print(f"Saving retrieval results to {retrieval_results_filename}")
        orig_qs_retrieval_results = get_retrieval_results(orig_qs, narrowed_qs, vectordb, retrieve_k)
        with open(retrieval_results_filename, "w", encoding="utf-8") as f:
            json.dump(orig_qs_retrieval_results, f, indent=4)

    elif cmd_choice in ["2", "create_summaries"]:
        print(f"Creating summaries from {retrieval_results_filename}")
        with open(retrieval_results_filename, "r", encoding="utf-8") as f:
            retrieval_results = json.load(f)

        summarizer_llm_model = os.environ.get("SUMMARIZER_LLM_MODEL_NAME", "openhermes")
        print(f"Summarizer SUMMARIZER_LLM_MODEL_NAME: {summarizer_llm_model}")

        # Extract Guru card texts so it can be summarized
        guru_card_texts = ingest.extract_qa_text_from_guru()

        summary_results = create_summaries(retrieval_results, summarizer_llm_model, guru_card_texts)

        with open(f"{filename_prefix}--{summarizer_llm_model}--summaries.json", "w", encoding="utf-8") as f:
            json.dump(summary_results, f, indent=4)


if __name__ == "__main__":
    print("""
    1. save_retrieval_results
    2. create_summaries""")
    dotenv.load_dotenv()
    if args := sys.argv[1:]:
        choice = args[0]
        print("Running option:", choice)
    else:
        print("What would you like to do?")
        choice = input()

    main(choice)
