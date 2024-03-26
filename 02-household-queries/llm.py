
from langchain_community.llms.ollama import Ollama
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

def ollama_client(model_name=None, callbacks=None, settings=None, print_to_stdout=False):
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

    print("LLM settings:", settings)
    # To connect via another URL: Ollama(base_url='http://localhost:11434', ...)
    return Ollama(model=model_name, callbacks=callbacks, **settings)

# Add LLM client for other LLMs here...
