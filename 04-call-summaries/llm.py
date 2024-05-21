import os

import anthropic
import dotenv
import google.generativeai as genai
from langchain_community.llms.ollama import Ollama
from openai import OpenAI

dotenv.load_dotenv()


class LLM:
    def __init__(
        self,
        client_name=None,
        model_name=None,
        max_tokens=1024,
        settings=None,
    ):
        self.client_name = client_name
        """Name of llm selection"""
        self.model_name = model_name
        """User friendly model name"""
        self.model_version = model_name
        """Exact model name being passed into the initializer"""
        self.max_tokens = max_tokens
        self.client = None
        self.settings = settings

    def get_client(self):
        """Retrieves the llm client"""
        if self.client_name == "ollama":
            if not settings:
                settings = {
                    # "temperature": 0.1,
                    # "system": "",
                    # "template": "",
                    # See https://github.com/langchain-ai/langchain/blob/master/libs/community/langchain_community/llms/ollama.py
                    "stop": None
                }
            if self.model_name is None:
                self.model_name = "openhermes"
            # To connect via another URL: Ollama(base_url='http://localhost:11434', ...)
            self.client = Ollama(model=self.model_version, **self.settings)

        elif self.client_name == "gemini":
            # Get a Google API key by following the steps after clicking on Get an API key button
            # at https://ai.google.dev/tutorials/setup
            GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
            print("LLM settings:", self.model_name, settings)

            if self.model_version is None:
                self.model_version = "gemini-1.5-flash-latest"
            elif self.model_name == "gemini-pro":
                self.model_version = "gemini-1.5-pro-latest"

            genai.configure(api_key=GOOGLE_API_KEY)
            if settings:
                genai.GenerationConfig(**self.settings)
            self.client = genai.GenerativeModel(self.model_name)

        elif self.client_name == "gpt":
            if self.model_name is None:
                self.model_version = "gpt-4o"
            elif self.model_name == "gpt3":
                self.model_version = "gpt-3.5-turbo"
            elif self.model_name == "gpt4":
                self.model_version = "gpt-4-turbo"

            # Get API key from https://platform.openai.com/api-keys
            OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
            self.client = OpenAI(api_key=OPENAI_API_KEY)  # Uses OPENAI_API_KEY

        elif self.client_name == "claude":
            self.model_version = "claude-3-opus-20240229"
            ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
            self.client = anthropic.Anthropic(
                api_key=ANTHROPIC_API_KEY,
            )

    def generate_text(self, prompt=None):
        """Generates response given prompt"""
        if self.client_name == "ollama":
            return self.client.invoke(prompt)
        elif self.client_name == "gemini":
            return self.client.generate(prompt).text
        elif self.client_name == "gpt":
            return (
                self.client.chat.completions.create(
                    model=self.model_version,
                    messages=[{"role": "user", "content": prompt}],
                )
                .choices[0]
                .message.content
            )
        elif self.client_name == "claude":
            generated_response = self.client.messages.create(
                model=self.model_version,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            ).content
            text_response = "\n".join(
                [text_block.text for text_block in generated_response]
            )

            return text_response
