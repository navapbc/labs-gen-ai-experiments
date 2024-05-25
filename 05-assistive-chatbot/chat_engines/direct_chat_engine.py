import logging

import utils

from . import _common

ENGINE_NAME = "Direct"

logger = logging.getLogger(__name__)


class DirectChatEngine:
    def __init__(self, settings):
        self.settings = settings
        self.client = _common.create_llm_client(settings)

    @utils.timer
    def get_response(self, query):
        logger.debug("Query: %s", query)
        response = self.client.submit(query)
        return response


def init_engine(settings):
    return DirectChatEngine(settings)
