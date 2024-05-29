import os

from openai import OpenAI

CLIENT_NAME = "openai"

# Model types: https://platform.openai.com/docs/models/model-endpoint-compatibility
_CHAT_MODELS = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"]
_LEGACY_MODELS = ["gpt-3.5-turbo-instruct"]
MODEL_NAMES = _CHAT_MODELS + _LEGACY_MODELS


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

    def generate_reponse(self, message):
        if self.model_name in _CHAT_MODELS:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": message}],
            )
            return response.choices[0].message.content
        elif self.model_name in _LEGACY_MODELS:
            response = self.client.completions.create(
                model=self.model_name,
                prompt=message,
            )
            return response.choices[0].text
        else:
            assert False, f"Unhandled LLM model: {self.model_name}"
