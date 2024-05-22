import os
import sys
import json
import dotenv

import dataclasses
from dataclasses import dataclass
from typing import List

import dspy

from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma

import dspy_engine
import ingest
import debugging

"""
Given a user question, decompose into simplier derived questions.
Then retrieve relevant Guru cards for each derived question.
Finally, provide a summary and quote for each Guru card.
"""


@dataclass
class CardResponseEntry:
    card_title: str
    associated_derived_qs: List[str]
    score_sum: float
    quotes: List[str]
    summary: str = None
    entire_text: str = None


@dataclass
class DerivedQuestionEntry:
    derived_question: str
    retrieved_cards: List[str] = None
    retrieved_chunks: List[str] = None
    retrieval_scores: List[float] = None


@dataclass
class GenerationResults:
    question: str
    derived_questions: List[DerivedQuestionEntry] = None
    cards: List[CardResponseEntry] = None


def init():
    dotenv.load_dotenv()
    return {
        "decompose_llm_name": os.environ.get("LLM_MODEL_NAME", "openhermes"),
        "decompose_llm": None,
        "decompose_predictor": None,
        "vectordb": None,
        "retrieve_k": int(os.environ.get("RETRIEVE_K", "4")),
        "summarizer_llm_name": os.environ.get("SUMMARIZER_LLM_MODEL_NAME", "openhermes"),
        "summarizer_llm": None,
        "summarizer_predictor": None,
        "guru_card_texts": None,
    }


def get_guru_card_texts():
    if settings["guru_card_texts"] is None:
        # Extract Guru card texts so it can be summarized
        settings["guru_card_texts"] = ingest.extract_qa_text_from_guru()
    return settings["guru_card_texts"]


def get_decompose_llm():
    if settings["decompose_llm"] is None:
        llm_model = settings["decompose_llm_name"]
        print(f"decompose_llm_name: {llm_model}")
        settings["decompose_llm"] = dspy_engine.create_llm_model(llm_model)
    return settings["decompose_llm"]


def get_summarizer_llm():
    if settings["summarizer_llm"] is None:
        llm_model = settings["summarizer_llm_name"]
        print(f"summarizer_llm_name: {llm_model}")
        settings["summarizer_llm"] = dspy_engine.create_llm_model(llm_model)
    return settings["summarizer_llm"]


def get_decompose_predictor():
    if settings["decompose_predictor"] is None:
        settings["decompose_predictor"] = create_predictor()
        print("Created decompose_predictor:", settings["decompose_predictor"])
    return settings["decompose_predictor"]


def get_summarizer_predictor():
    if settings["summarizer_predictor"] is None:
        settings["summarizer_predictor"] = create_summarizer()
    return settings["summarizer_predictor"]


@debugging.timer
def create_predictor():
    class DecomposeQuestion(dspy.Signature):
        """Decompose into multiple questions so that we can search for relevant SNAP and food assistance eligibility rules. \
Be concise -- only respond with JSON. Only output the questions as a JSON list: ["question1", "question2", ...]. \
The question is: {question}"""

        # TODO: Incorporate https://gist.github.com/hugodutka/6ef19e197feec9e4ce42c3b6994a919d

        question = dspy.InputField()
        answer = dspy.OutputField(desc='["question1", "question2", ...]')

    return dspy.Predict(DecomposeQuestion)


def get_vectordb():
    if settings["vectordb"] is None:
        settings["vectordb"] = create_vectordb()
    return settings["vectordb"]


def create_summarizer():
    class SummarizeCardGivenQuestion(dspy.Signature):
        """Summarize the following context into 1 sentence without explicitly answering the question(s): {context_question}

        Context: {context}
        """

        context_question = dspy.InputField()
        context = dspy.InputField()
        answer = dspy.OutputField()

    return dspy.Predict(SummarizeCardGivenQuestion)


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
def on_question(question):
    gen_results = GenerationResults(question)

    # TODO: retry if don't get JSON array response
    with dspy.context(lm=get_decompose_llm()):
        derived_questions = generate_derived_questions(get_decompose_predictor(), question)

    collect_retrieved_cards(derived_questions, gen_results)

    with dspy.context(lm=get_summarizer_llm()):
        create_summaries(gen_results, get_summarizer_predictor(), get_guru_card_texts())

    return gen_results


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


def collect_retrieved_cards(derived_qs, gen_results):
    retrieve_k = settings["retrieve_k"]
    print("RETRIEVE_K:", retrieve_k)
    gen_results.derived_questions = retrieve_cards(derived_qs, get_vectordb(), retrieve_k)
    gen_results.cards = collate_by_card_score_sum(gen_results.derived_questions)


@debugging.timer
def collate_by_card_score_sum(derived_question_entries):
    all_retrieved_cards = dict()
    for dq_entry in derived_question_entries:
        scores = dq_entry.retrieval_scores
        for i, card in enumerate(dq_entry.retrieved_cards):
            all_retrieved_cards[card] = all_retrieved_cards.get(card, 0) + scores[i]

    card_to_dqs = {}
    card_to_quotes = {}
    for dq_entry in derived_question_entries:
        derived_question = dq_entry.derived_question
        for card in dq_entry.retrieved_cards:
            if card not in card_to_dqs:
                card_to_dqs[card] = set()
            card_to_dqs[card].add(derived_question)

        for card, quote in zip(dq_entry.retrieved_cards, dq_entry.retrieved_chunks):
            if card not in card_to_quotes:
                card_to_quotes[card] = set()
            if quote != card:
                card_to_quotes[card].add(quote)

    all_retrieved_cards = dict(
        sorted(
            all_retrieved_cards.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )

    return [
        CardResponseEntry(card, list(card_to_dqs[card]), score, list(card_to_quotes[card]))
        for card, score in all_retrieved_cards.items()
    ]


@debugging.timer
def retrieve_cards(derived_qs, vectordb, retrieve_k=5):
    results = []  # list of DerivedQuestionEntry
    # print(f"Processing user question {qa_dict['id']}: with {len(derived_qs)} derived questions")
    for q in derived_qs:
        retrieval_tups = vectordb.similarity_search_with_relevance_scores(q, k=retrieve_k)
        retrieval = [tup[0] for tup in retrieval_tups]
        retrieved_cards = [doc.metadata["source"] for doc in retrieval]
        retrieved_chunks = [doc.page_content for doc in retrieval]
        scores = [tup[1] for tup in retrieval_tups]
        results.append(DerivedQuestionEntry(q, retrieved_cards, retrieved_chunks, scores))
    return results


@debugging.timer
def create_summaries(gen_results, summarizer, guru_card_texts):
    print(f"Summarizing {len(gen_results.cards)} retrieved cards...")
    for i, card_entry in enumerate(gen_results.cards):
        # Limit summarizing of Guru cards based on score and card count
        if i > 2 and card_entry.score_sum < 0.3:
            continue
        card_text = guru_card_texts[card_entry.card_title]
        card_entry.entire_text = "\n".join([card_entry.card_title, card_text])
        # Summarize based on derived question and original question
        # Using only the original question causes the LLM to try to answer the question.
        context_questions = " ".join(card_entry.associated_derived_qs + [gen_results.question])
        print(f"  {i}. Summarizing {card_entry.card_title}...")
        prediction = summarizer(context_question=context_questions, context=card_entry.entire_text)
        card_entry.summary = prediction.answer


@debugging.timer
def format_response(gen_results):
    resp = ["==="]
    resp.append("Q: {gen_results.question}")

    for i, dq in enumerate(gen_results.derived_questions):
        resp.append(f"DQ {i}: {dq.derived_question}")

    resp.append("Guru cards:")
    for card in gen_results.cards:
        if card.summary:
            resp += ["---", card.card_title, f"  Summary: {card.summary}"] + [f'  > "{q}"' for q in card.quotes]

    return "\n".join(resp)


settings = init()
if __name__ == "__main__":
    if args := sys.argv[1:]:
        user_question = args[0]
        print("Running option:", user_question)
    else:
        user_question = "The client's son is 20, is still living with them, but has his own job and buys his own food. Does the client have to list him on the application? If so, do we need to include the dependent's income for SNAP?"

    generated_results = on_question(user_question)
    print(json.dumps(dataclasses.asdict(generated_results), indent=2))

    print(format_response(generated_results))
