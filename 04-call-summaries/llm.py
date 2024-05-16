import os

import anthropic
import dotenv
import google.generativeai as genai
from langchain_community.llms.ollama import Ollama
from openai import OpenAI

dotenv.load_dotenv()


def get_transcript(file_path="./transcript.txt"):
    file = open(file_path, encoding="utf-8")
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
    model_name="gemini-1.5-flash-latest",
    prompt=None,
    settings=None,
):
    # Get a Google API key by following the steps after clicking on Get an API key button
    # at https://ai.google.dev/tutorials/setup
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

    print("LLM settings:", model_name, settings)

    genai.configure(api_key=GOOGLE_API_KEY)
    if settings:
        genai.GenerationConfig(**settings)
    model = genai.GenerativeModel(model_name)
    return model.generate_content(prompt)


def gpt3_5(prompt, model="gpt-3.5-turbo"):
    # Get API key from https://platform.openai.com/api-keys
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    openai_client = OpenAI(api_key=OPENAI_API_KEY)  # Uses OPENAI_API_KEY
    return (
        openai_client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}]
        )
        .choices[0]
        .message.content
    )


def gpt_4_turbo(prompt):
    return gpt3_5(prompt, model="gpt-4-turbo")


def gpt_4o(prompt):
    return gpt3_5(prompt, model="gpt-4o")


def claude(prompt, model="claude-3-opus-20240229", max_tokens=1024):
    # Get API key from https://console.anthropic.com/settings/keys
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

    client = anthropic.Anthropic(
        api_key=ANTHROPIC_API_KEY,
    )
    generated_response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    ).content
    text_response = "\n".join([text_block.text for text_block in generated_response])

    return text_response
