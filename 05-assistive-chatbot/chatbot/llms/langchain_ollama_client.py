import logging
import os

from langchain_community.llms.ollama import Ollama

logger = logging.getLogger(__name__)

CLIENT_NAME = "langchain.ollama"
MODEL_NAMES = ["openhermes", "llama2", "llama2:chat", "llama3", "mistral", "mistral:instruct"]


def requirements_satisfied():
    if os.environ.get("ENV") == "PROD":
        # Exclude Ollama models in production b/c it requires a local Ollama installation
        return False
    return True


def init_client(model_name, settings):
    return LangchainOllamaClient(model_name, settings)


class LangchainOllamaClient:
    def __init__(self, model_name, settings):
        self.settings = settings
        # if not settings:
        #     settings = {
        #         # "system": "",
        #         # "template": "",
        #         # See https://github.com/langchain-ai/langchain/blob/master/libs/community/langchain_community/llms/ollama.py
        #         "stop": None
        #     }
        logger.info("Creating LLM client '%s' with %s", model_name, self.settings)
        self.client = Ollama(model=model_name, **self.settings)

    def generate_reponse(self, message):
        return self.client.invoke(message)
