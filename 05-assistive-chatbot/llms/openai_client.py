from openai import OpenAI

CLIENT_NAME = "openai"
# These names will be associated with this Python module
MODEL_NAMES = ["gpt-3.5-turbo", "gpt-3.5-turbo-instruct", "gpt-4", "gpt-4-turbo", "gpt-4o"]


class OpenaiLlmClient:
    name = "OpenAI"

    def __init__(self, model_name, settings):
        self.model_name = model_name
        self.settings = settings
        self.client = OpenAI()

    def submit(self, message):
        return f"Submitted to OpenAI LLM {self.model_name}: {message}"


# This function is expected
def init_client(model_name, settings):
    return OpenaiLlmClient(model_name, settings)
