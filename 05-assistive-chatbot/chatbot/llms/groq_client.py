import logging
import os

from groq import Groq

logger = logging.getLogger(__name__)

CLIENT_NAME = "groq"
MODEL_NAMES = ["llama3-70b-8192", "mixtral-8x7b-32768"]


def requirements_satisfied():
    if not os.environ.get("GROQ_API_KEY"):
        return False
    return True


def init_client(model_name, settings):
    return GroqClient(model_name, settings)


class GroqClient:
    INIT_ARGS = ["timeout", "max_retries", "default_headers", "default_query", "base_url", "http_client"]

    def __init__(self, model_name, settings):
        self.model_name = model_name
        self.settings = settings

        init_settings = {k: settings[k] for k in settings if k in self.INIT_ARGS}
        logger.info("Creating LLM client '%s' with %s", model_name, init_settings)
        self.client = Groq(**init_settings)

    def generate_reponse(self, message):
        chat_completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": message}], model=self.model_name, **self.settings
        )

        return chat_completion.choices[0].message.content
