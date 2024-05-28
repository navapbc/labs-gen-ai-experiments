import logging
import os

import dspy

from chatbot import engines, utils

logger = logging.getLogger(__name__)

ENGINE_NAME = "Summaries"


def requirements_satisfied():
    if not os.environ.get("SUMMARIZER_LLM_MODEL_NAME"):
        return False
    return True


def init_engine(settings):
    return SummariesChatEngine(settings)


class SummariesChatEngine:
    def __init__(self, settings):
        self.settings = settings
        self.summarizer = create_summarizer()
        if "predictor" not in settings:
            settings["predictor"] = self.summarizer_predictor
        logger.info("Creating LLM client with %s", settings)
        self.client = engines.create_llm_client(settings)

    def summarizer_predictor(self, message):
        # logger.info("Summarizing: %s using %s", message, summarizer)
        prediction = self.summarizer(context_question=message, context="")
        return prediction.answer

    @utils.timer
    def gen_response(self, query):
        response = self.client.generate_reponse(query)
        # TODO: decompose query
        # TODO: create summaries
        return response


def create_summarizer():
    class SummarizeCardGivenQuestion(dspy.Signature):
        """Summarize the following context into 1 sentence without explicitly answering the question(s): {context_question}

        Context: {context}
        """

        context_question = dspy.InputField()
        context = dspy.InputField()
        answer = dspy.OutputField()

    return dspy.Predict(SummarizeCardGivenQuestion)
