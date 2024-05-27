import logging

from chatbot import engines, utils

ENGINE_NAME = "Direct"

logger = logging.getLogger(__name__)


def init_engine(settings):
    return DirectChatEngine(settings)


class DirectChatEngine:
    def __init__(self, settings):
        self.settings = settings
        self.client = engines.create_llm_client(settings)

    @utils.timer
    def gen_response(self, query):
        logger.debug("Query: %s", query)
        response = self.client.submit(query)
        return response
