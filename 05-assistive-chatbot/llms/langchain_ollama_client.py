from langchain_community.llms.ollama import Ollama

CLIENT_NAME = "langchain.ollama"
MODEL_NAMES = ["openhermes", "llama2", "mistral"]


class LangchainClient:
    def __init__(self, model_name, settings):
        self.client = Ollama(model=model_name, **settings)

    def submit(self, message):
        return self.client.invoke(message)


def init_client(model_name, settings):
    return LangchainClient(model_name, settings)
