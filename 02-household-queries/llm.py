import dotenv

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.llms.ollama import Ollama
from langchain_community.llms import GPT4All
from langchain_google_genai import ChatGoogleGenerativeAI

import os

dotenv.load_dotenv()


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
            # See https://github.com/langchain-ai/langchain/blob/master/libs/community/langchain_community/llms/ollama.py
            "stop": None
        }

    print("LLM settings:", model_name, settings)
    # To connect via another URL: Ollama(base_url='http://localhost:11434', ...)
    return Ollama(model=model_name, callbacks=callbacks, **settings)


# Add LLM client for other LLMs here...
def gpt4all_client(
    model_path="./models/mistral-7b-instruct-v0.1.Q4_0.gguf",
    callbacks=None,
    settings=None,
    print_to_stdout=False,
):
    # Open source option
    # download Mistral at https://mistral.ai/news/announcing-mistral-7b/
    if not callbacks:
        callbacks = []
    if print_to_stdout:
        callbacks.append(StreamingStdOutCallbackHandler())

    if not settings:
        settings = {
            # "temp": 0.1,
            # See https://github.com/langchain-ai/langchain/blob/master/libs/community/langchain_community/llms/gpt4all.py
            "stop": None
        }

    print("LLM settings:", settings)

    return GPT4All(model=model_path, max_tokens=1000, verbose=True, repeat_last_n=0, **settings)


def google_gemini_client(model_name="gemini-pro", callbacks=None, settings=None, print_to_stdout=False):
    # Get a Google API key by following the steps after clicking on Get an API key button
    # at https://ai.google.dev/tutorials/setup
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    if not callbacks:
        callbacks = []
    if print_to_stdout:
        callbacks.append(StreamingStdOutCallbackHandler())

    if not settings:
        settings = {
            # "temperature": 0.1,
            # "top_k": 1
            # See https://github.com/langchain-ai/langchain/blob/master/libs/community/langchain_community/llms/gpt4all.py
            "stop": None
        }

    print("LLM settings:", settings)
    return ChatGoogleGenerativeAI(
        model=model_name,
        verbose=True,
        google_api_key=GOOGLE_API_KEY,
        convert_system_message_to_human=True,
        **settings,
    )
