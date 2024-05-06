import dotenv

from langchain_community.llms.ollama import Ollama
import google.generativeai as genai
from openai import OpenAI
import os

dotenv.load_dotenv()


def get_transcript(file_path="./transcript.txt"):
    file = open(file_path)
    content = file.read()
    return content


def ollama_client(
    model_name=None,
    prompt=None,
    callbacks=None,
    settings=None,
):
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
    return Ollama(model=model_name, callbacks=callbacks, **settings).invoke(prompt)


def google_gemini_client(
    model_name="gemini-pro",
    prompt=None,
    settings={},
):
    # Get a Google API key by following the steps after clicking on Get an API key button
    # at https://ai.google.dev/tutorials/setup
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

    print("LLM settings:", model_name, settings)

    genai.configure(api_key=GOOGLE_API_KEY)
    genai.GenerationConfig(**settings)
    model = genai.GenerativeModel(model_name)
    return model.generate_content(prompt)


def gpt3_5(prompt, model="gpt-3.5-turbo"):
    OPEN_AI_API_KEY = os.environ.get("OPEN_AI_API_KEY")
    openai_client = OpenAI(api_key=OPEN_AI_API_KEY)  # Uses OPENAI_API_KEY
    return (
        openai_client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}]
        )
        .choices[0]
        .message.content
    )


def gpt_4_turbo(prompt):
    return gpt3_5(prompt, model="gpt-4-turbo")
