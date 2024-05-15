import os
import sys
import json
import dataclasses
from dataclasses import dataclass

import dspy

from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma

import dspy_engine
import debugging

from typing import List

"""
Given a user question, decompose into simplier derived questions.
Then retrieve relevant Guru cards for each derived question.
Finally, provide a summary and quote for each Guru card.
"""


@dataclass
class CardResponseEntry:
    card: str
    score_sum: float
    summary: str = ""
    quote: str = ""


@dataclass
class DerivedQuestionEntry:
    derived_question: str
    retrieved_cards: List[str] = None
    retrieval_scores: List[float] = None


@dataclass
class GenerationResults:
    question: str
    derived_questions: List[DerivedQuestionEntry] = None
    cards: List[CardResponseEntry] = None


def on_question(question):
    gen_results = GenerationResults(question)
    derived_questions = main1_decompose_user_questions(question)

    main2_retrieve_cards(derived_questions, gen_results)

    # response = derived_questions, "guru_cards": [dataclasses.asdict(r1)]}
    return json.dumps(dataclasses.asdict(gen_results), indent=2)


def main1_decompose_user_questions(question):
    llm_model = os.environ.get("LLM_MODEL_NAME", "openhermes")
    print(f"LLM_MODEL_NAME: {llm_model}")
    predictor = get_question_transformer_llm(llm_model)
    print("Predictor created", predictor)
    return generate_derived_questions(predictor, question)


def get_question_transformer_llm(llm_model):
    # TODO: create only once
    return create_predictor(llm_model)


@debugging.timer
def create_predictor(llm_choice):
    assert llm_choice is not None, "llm_choice must be specified."
    dspy.settings.configure(
        lm=dspy_engine.create_llm_model(llm_choice)  # , rm=create_retriever_model()
    )
    print("LLM model created", dspy.settings.lm)

    class DecomposeQuestion(dspy.Signature):
        """Decompose into multiple questions so that we can search for relevant SNAP and food assistance eligibility rules. \
Be concise -- only respond with JSON. Only output the questions as a JSON list: ["question1", "question2", ...]. \
The question is: {question}"""

        # TODO: Incorporate https://gist.github.com/hugodutka/6ef19e197feec9e4ce42c3b6994a919d

        question = dspy.InputField()
        answer = dspy.OutputField(desc='["question1", "question2", ...]')

    return dspy.Predict(DecomposeQuestion)


@debugging.timer
def generate_derived_questions(predictor, question):
    pred = predictor(question=question)
    print("Answer:", pred.answer)
    derived_questions = json.loads(pred.answer)
    if "Answer" in derived_questions:
        # For OpenAI 'gpt-4-turbo' in json mode
        derived_questions = derived_questions["Answer"]
    print("  => ", derived_questions)
    return derived_questions


def main2_retrieve_cards(derived_qs, gen_results):
    vectordb = create_vectordb()

    llm_model = os.environ.get("LLM_MODEL_NAME", "openhermes")
    print(f"LLM_MODEL_NAME: {llm_model}")
    retrieve_k = int(os.environ.get("RETRIEVE_K", "4"))
    print("RETRIEVE_K:", retrieve_k)
    gen_results.derived_questions = retrieve_cards(derived_qs, vectordb, retrieve_k)
    gen_results.cards = collate_by_card_score_sum(gen_results.derived_questions)

def collate_by_card_score_sum(derived_question_entries):
    all_retrieved_cards = dict()
    for dq_entry in derived_question_entries:
        scores = dq_entry.retrieval_scores
        for i, card in enumerate(dq_entry.retrieved_cards):
            all_retrieved_cards[card] = all_retrieved_cards.get(card, 0) + scores[i]

    all_retrieved_cards = dict(
        sorted(
            all_retrieved_cards.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )

    return [CardResponseEntry(card, score) for card, score in all_retrieved_cards.items()]


@debugging.timer
def create_vectordb():
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    return Chroma(
        embedding_function=embeddings,
        # Must use collection_name="langchain" -- https://github.com/langchain-ai/langchain/issues/10864#issuecomment-1730303411
        collection_name="langchain",
        persist_directory="./chroma_db",
    )


@debugging.timer
def retrieve_cards(derived_qs, vectordb, retrieve_k=5):
    results = []  # list of DerivedQuestionEntry
    # print(f"Processing user question {qa_dict['id']}: with {len(derived_qs)} derived questions")
    for q in derived_qs:
        retrieval_tups = vectordb.similarity_search_with_relevance_scores(q, k=retrieve_k)
        retrieval = [tup[0] for tup in retrieval_tups]
        retrieved_cards = [doc.metadata["source"] for doc in retrieval]
        scores = [tup[1] for tup in retrieval_tups]
        results.append(DerivedQuestionEntry(q, retrieved_cards, scores))
    return results


if __name__ == "__main__":
    if args := sys.argv[1:]:
        user_question = args[0]
        print("Running option:", user_question)
    else:
        user_question = "SNAP for childcare?"

    resp = on_question(user_question)
    print(resp)
