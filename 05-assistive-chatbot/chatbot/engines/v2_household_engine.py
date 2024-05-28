import os

from chatbot import engines, utils

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
        self.client = engines.create_llm_client(settings)

    @utils.timer
    def gen_response(self, query):
        response = self.client.submit(query)
        # TODO: create summaries
        return response
