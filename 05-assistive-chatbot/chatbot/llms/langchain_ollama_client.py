from langchain_community.llms.ollama import Ollama

CLIENT_NAME = "langchain.ollama"
MODEL_NAMES = ["openhermes", "llama2", "mistral"]


def init_client(model_name, settings):
    return LangchainClient(model_name, settings)


class LangchainClient:
    def __init__(self, model_name, settings):
        # if not settings:
        #     settings = {
        #         # "system": "",
        #         # "template": "",
        #         # See https://github.com/langchain-ai/langchain/blob/master/libs/community/langchain_community/llms/ollama.py
        #         "stop": None
        #     }
        self.client = Ollama(model=model_name, **settings)

    def submit(self, message):
        return self.client.invoke(message)
