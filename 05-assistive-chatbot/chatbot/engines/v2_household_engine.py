import json
import logging
import os
from dataclasses import dataclass
from functools import cached_property
from typing import List, Optional

from chatbot import engines, guru_cards, utils, vector_db

logger = logging.getLogger(__name__)

ENGINE_NAME = "Summaries"


def init_engine(settings):
    return SummariesChatEngine(settings)


@dataclass
class CardResponseEntry:
    card_title: str
    associated_derived_qs: List[str]
    score_sum: float
    quotes: List[str]
    summary: Optional[str] = None
    entire_text: Optional[str] = None


@dataclass
class DerivedQuestionEntry:
    derived_question: str
    retrieved_cards: Optional[List[str]] = None
    retrieved_chunks: Optional[List[str]] = None
    retrieval_scores: Optional[List[float]] = None


@dataclass
class GenerationResults:
    question: str
    derived_questions: Optional[List[DerivedQuestionEntry]] = None
    cards: Optional[List[CardResponseEntry]] = None


class Prompts:
    decomposer = """Rephrase and decompose into multiple questions so that we can search for relevant public benefits eligibility requirements. \
    Be concise -- only respond with JSON. Only output the questions as a JSON list: ["question1", "question2", ...]. \
    The question is: {question}"""

    summarizer = """Summarize the following context into 1 sentence without explicitly answering the question(s): {context_question}

            Context: {context}
            """


## Summaries Chat Engine


class SummariesChatEngine:
    def __init__(self, orig_settings):
        if orig_settings["model"].startswith("dspy ::") or orig_settings["model2"].startswith("dspy ::"):
            assert False, "Summaries chat engine does not support DSPy models -- use Summaries-DSPy instead."

        # Make a copy of the settings so that we can modify them
        self.settings = orig_settings.copy()

        # Use the same vector DB configuration as ingest-guru-cards.py
        self.vectordb_wrapper = vector_db.ingest_vectordb_wrapper
        self.retrieve_k = int(self.settings.pop("retrieve_k"))

        # TODO: ingestigate if this should be set to true
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

        self.prompts = Prompts()
        self.decomposer_client = engines.create_llm_client(self.settings.copy())

        if "model2" in self.settings:
            self.settings["model"] = self.settings.pop("model2")
        if "temperature2" in self.settings:
            self.settings["temperature"] = self.settings.pop("temperature2")
        self.summarizer_client = engines.create_llm_client(self.settings.copy())

        # TODO for scalability: replace with DB lookup
        self.guru_card_texts = guru_cards.GuruCardsProcessor().extract_qa_text_from_guru()

    @utils.timer
    def gen_response(self, query):
        gen_results = GenerationResults(query)

        for i in range(1, 4):  # retry loop
            if i > 1:
                logger.warning("Retrying to get parsable JSON response -- attempt %i", i)
                # TODO: also send notification to UI by adding a message to GenerationResults
            try:
                response = self.call_llm(self.decomposer_client, self.prompts.decomposer, question=query)
                derived_questions = json.loads(response)

                logger.info("Derived questions: %s", derived_questions)
                break  # exit retry loop
            except json.JSONDecodeError as e:
                logger.error("Error decomposing question: %s", e)
                derived_questions = []

        collect_retrieved_cards(derived_questions, self.vectordb_wrapper.vectordb, self.retrieve_k, gen_results)
        logger.debug("gen_results: %s", gen_results)

        populate_summaries(gen_results, self.guru_card_texts, self.summarizer)
        return gen_results

    def summarizer(self, **kwargs):
        return self.call_llm(self.summarizer_client, self.prompts.summarizer, **kwargs)

    def call_llm(self, llm_client, prompt_template: str, **template_inputs):
        prompt = prompt_template.format(**template_inputs)
        logger.debug("Prompt: %s", prompt)
        response = llm_client.generate_reponse(prompt)
        logger.debug("Response object: %s", response)
        return response


## Non-LLM Helper functions


def collect_retrieved_cards(derived_qs, vectordb, retrieve_k, gen_results):
    logger.debug("RETRIEVE_K: %i", retrieve_k)
    gen_results.derived_questions = retrieve_cards(derived_qs, vectordb, retrieve_k)
    gen_results.cards = collate_by_card_score_sum(gen_results.derived_questions)


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


def retrieve_cards(derived_qs, vectordb, retrieve_k=5):
    results = []
    for q in derived_qs:
        retrieval_tups = vectordb.similarity_search_with_relevance_scores(q, k=retrieve_k)
        retrieval = [tup[0] for tup in retrieval_tups]
        retrieved_cards = [doc.metadata["source"] for doc in retrieval]
        retrieved_chunks = [doc.page_content for doc in retrieval]
        scores = [tup[1] for tup in retrieval_tups]
        results.append(DerivedQuestionEntry(q, retrieved_cards, retrieved_chunks, scores))
    return results


def populate_summaries(gen_results, guru_card_texts, summarizer):
    logger.info("Summarizing %i retrieved cards...", len(gen_results.cards))
    for i, card_entry in enumerate(gen_results.cards):
        # Limit summarizing of Guru cards based on score and card count
        if i > 2 and card_entry.score_sum < 0.3:
            continue
        card_text = guru_card_texts[card_entry.card_title]
        card_entry.entire_text = "\n".join([card_entry.card_title, card_text])
        # Summarize based on derived question and original question
        # Using only the original question causes the LLM to try to answer the question.
        context_questions = " ".join(card_entry.associated_derived_qs + [gen_results.question])
        logger.info("  %i. Summarizing: %s", i, card_entry.card_title)
        card_entry.summary = summarizer(context_question=context_questions, context=card_entry.entire_text)
