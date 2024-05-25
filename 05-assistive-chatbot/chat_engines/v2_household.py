import utils

from . import _common

ENGINE_NAME = "Summaries"


class SummariesChatEngine:
    def __init__(self, settings):
        self.settings = settings
        self.client = _common.create_llm_client(settings)

    @utils.timer
    def get_response(self, query):
        response = self.client.submit(query)
        # TODO: create summaries
        return response


def init_engine(settings):
    return SummariesChatEngine(settings)
