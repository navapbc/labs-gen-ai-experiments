import logging
import os

import google.generativeai as genai

logger = logging.getLogger(__name__)

CLIENT_NAME = "google"
MODEL_NAMES = ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"]


def requirements_satisfied():
    if not os.environ.get("GOOGLE_API_KEY"):
        return False
    return True


def init_client(model_name, settings):
    return GeminiLlmClient(model_name, settings)


class GeminiLlmClient:
    def __init__(self, model_name, settings):
        logger.info("Creating LLM client '%s' with %s", model_name, settings)
        if settings is not None:
            genai.GenerationConfig(**settings)
        self.client = genai.GenerativeModel(model_name)

    def generate_reponse(self, message):
        return self.client.generate_content(message).text
