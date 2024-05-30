import logging
import os

from langchain_google_genai import ChatGoogleGenerativeAI

CLIENT_NAME = "langchain.google"
MODEL_NAMES = ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"]


def requirements_satisfied(_settings):
    if not os.environ.get("GOOGLE_API_KEY"):
        return False
    return True


def init_client(model_name, settings):
    return LangchainGoogleClient(model_name, settings)


class LangchainGoogleClient:
    def __init__(self, model_name, settings):
        self.client = ChatGoogleGenerativeAI(model=model_name, **settings)

    def generate_reponse(self, message):
        # invoke() returns langchain_core.messages.ai.AIMessage
        return self.client.invoke(message).content
