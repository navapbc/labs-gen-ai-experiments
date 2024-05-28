import os

from openai import OpenAI

CLIENT_NAME = "openai"
# These names will be associated with this Python module
MODEL_NAMES = ["gpt-3.5-turbo", "gpt-3.5-turbo-instruct", "gpt-4", "gpt-4-turbo", "gpt-4o"]


def requirements_satisfied():
    if not os.environ.get("OPENAI_API_KEY"):
        return False
    return True


def init_client(model_name, settings):
    return OpenaiLlmClient(model_name, settings)


class OpenaiLlmClient:
    def __init__(self, model_name, settings):
        self.model_name = model_name
        self.settings = settings
        self.client = OpenAI()

    def submit(self, message):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": message}],
        )
        return response.choices[0].message.content
