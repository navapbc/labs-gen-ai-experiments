import dataclasses
import json
import logging
import os
from dataclasses import dataclass
from typing import List

import dspy  # type: ignore[import-untyped]

from chatbot import engines, utils

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


class SummariesChatEngine:
    def __init__(self, settings):
        self.settings = settings

        self.decomposer = create_question_decomposer()
        if "predictor" not in settings:
            settings["predictor"] = self.decomposer_predictor
        logger.info("Creating DecomposeQuestion LLM client with %s", settings)
        self.decomposer_client = engines.create_llm_client(settings)

        self.summarizer = create_summarizer()
        settings["predictor"] = None
        logger.info("Creating Summarize LLM client with %s", settings)
        self.summarizer_client = engines.create_llm_client(settings)

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
            self.create_summaries(gen_results, self.summarizer, self.get_guru_card_texts())

        return json.dumps(dataclasses.asdict(gen_results), indent=2)

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
        # retrieve_k = settings["retrieve_k"]
        # print("RETRIEVE_K:", retrieve_k)
        # gen_results.derived_questions = retrieve_cards(derived_qs, get_vectordb(), retrieve_k)
        # gen_results.cards = collate_by_card_score_sum(gen_results.derived_questions)
        gen_results.cards = [CardResponseEntry("A", ["B"], 0.5, ["C"])]

    def get_guru_card_texts(self):
        # if settings["guru_card_texts"] is None:
        #     # Extract Guru card texts so it can be summarized
        #     settings["guru_card_texts"] = ingest.extract_qa_text_from_guru()
        # return settings["guru_card_texts"]
        return {"A": "B", "C": "D"}

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
