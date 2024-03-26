from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from langchain_community.llms.ollama import Ollama


def create_llm(model_name, callbacks=None, settings=None, print_to_stdout=False):
    if not callbacks:
        callbacks = []
    if print_to_stdout:
        callbacks.append(StreamingStdOutCallbackHandler())

    if not settings:
        settings = {
            # "temperature": 0.1,
            # "system": "",
            # "template": "",
            # See langchain_community/llms/ollama.py
            "stop": None
        }

    # To connect via URL: Ollama(base_url='http://localhost:11434', model=llm_model_name, callbacks=callbacks)
    # return Ollama(base_url='http://localhost:8000', model=llm_model_name, callbacks=callbacks)
    return Ollama(model=model_name, callbacks=callbacks, **settings)
