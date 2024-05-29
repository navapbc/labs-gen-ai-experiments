import json
import logging
import os
from dataclasses import dataclass
from typing import List, Optional

import dspy  # type: ignore[import-untyped]

from chatbot import engines, guru_cards, utils, vector_db

logger = logging.getLogger(__name__)

ENGINE_NAME = "Summaries"


def requirements_satisfied():
    if not os.environ.get("SUMMARIZER_LLM_MODEL_NAME"):
        return False
    return True


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


class SummariesChatEngine:
    def __init__(self, orig_settings):
        # Make a copy of the settings so that we can modify them
        self.settings = orig_settings.copy()

        assert self.settings["model"].startswith("dspy ::"), f"Expecting DSPy LLM but got: {self.settings['model']}"

        # Use the same vector DB configuration as ingest-guru-cards.py
        self.vectordb_wrapper = vector_db.ingest_vectordb_wrapper
        self.retrieve_k = int(self.settings.pop("retrieve_k"))

        self.decomposer = create_question_decomposer()
        if "predictor" not in self.settings:
            self.settings["predictor"] = self.decomposer_predictor
        logger.info("Creating DecomposeQuestion LLM client with %s", self.settings)
        self.decomposer_client = engines.create_llm_client(self.settings)

        self.summarizer = create_summarizer()
        self.settings["predictor"] = None
        logger.info("Creating Summarize LLM client with %s", self.settings)
        self.summarizer_client = engines.create_llm_client(self.settings)

        # TODO: ingestigate if this should be set to true
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

        self.guru_card_texts = guru_cards.GuruCardsProcessor().extract_qa_text_from_guru()

    def decomposer_predictor(self, message):
        logger.info("Decomposing: %s", message)
        prediction = self.decomposer(question=message)
        return prediction.answer

    @utils.timer
    def gen_response(self, query):
        gen_results = GenerationResults(query)

        # derived_questions = self.decomposer_client.generate_reponse(query)
        with dspy.context(lm=self.decomposer_client.llm):
            derived_questions = self.generate_derived_questions(query)
        logger.info("Derived questions: %s", derived_questions)

        self.collect_retrieved_cards(derived_questions, gen_results)
        logger.info("gen_results: %s", gen_results)

        with dspy.context(lm=self.summarizer_client.llm):
            self.create_summaries(gen_results, self.summarizer, self.guru_card_texts)

        return gen_results

    def generate_derived_questions(self, question):
        logger.info("Decomposing: %s", question)
        pred = self.decomposer(question=question)
        # if CALL_OPENAI_DIRECTLY:  # debugging difference between using OpenAI via DSPy
        #     # print("pred", pred)
        #     call_openai_directly(question)
        logger.info("Answer: %s", pred.answer)
        try:
            derived_questions = json.loads(pred.answer)
        except Exception as e:  # in case LLM doesn't generate valid JSON
            print("!!! Error:", e)
            # traceback.print_exc()
            # # retry using direct call to OpenAI since DSPy caches responses and hence will return the same response
            # for i in range(3):
            #     print("Retrying by calling OpenAI directly")
            #     # TODO: also send notification to UI by adding a message to GenerationResults
            #     response = call_openai_directly(question)
            #     try:
            #         derived_questions = json.loads(response)
            #         break  # out of for-loop
            #     except Exception as e2:
            #         print("!!!! Error:", e2)
            #         traceback.print_exc()

        if "Answer" in derived_questions:
            # For OpenAI 'gpt-4-turbo' in json mode
            derived_questions = derived_questions["Answer"]
        print("  => ", derived_questions)
        return derived_questions

    def collect_retrieved_cards(self, derived_qs, gen_results):
        logger.debug("RETRIEVE_K: %i", self.retrieve_k)
        gen_results.derived_questions = self.retrieve_cards(derived_qs, self.vectordb_wrapper.vectordb, self.retrieve_k)
        gen_results.cards = self.collate_by_card_score_sum(gen_results.derived_questions)

    def retrieve_cards(self, derived_qs, vectordb, retrieve_k=5):
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

    def collate_by_card_score_sum(self, derived_question_entries):
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

    def create_summaries(self, gen_results, summarizer, guru_card_texts):
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
            prediction = summarizer(context_question=context_questions, context=card_entry.entire_text)
            card_entry.summary = prediction.answer


def create_question_decomposer():
    class DecomposeQuestion(dspy.Signature):
        """Rephrase and decompose into multiple questions so that we can search for relevant public benefits eligibility requirements. \
Be concise -- only respond with JSON. Only output the questions as a JSON list: ["question1", "question2", ...]. \
The question is: {question}"""

        # TODO: Incorporate https://gist.github.com/hugodutka/6ef19e197feec9e4ce42c3b6994a919d

        question = dspy.InputField()
        answer = dspy.OutputField(desc='["question1", "question2", ...]')

    return dspy.Predict(DecomposeQuestion)


def create_summarizer():
    class SummarizeCardGivenQuestion(dspy.Signature):
        """Summarize the following context into 1 sentence without explicitly answering the question(s): {context_question}

        Context: {context}
        """

        context_question = dspy.InputField()
        context = dspy.InputField()
        answer = dspy.OutputField()

    return dspy.Predict(SummarizeCardGivenQuestion)
