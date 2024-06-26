import logging
import os

import dspy  # type: ignore[import-untyped]

CLIENT_NAME = "dspy"

_OLLAMA_LLMS = ["openhermes", "llama2", "llama2:chat", "llama3", "mistral", "mistral:instruct"]
_OPENAI_LLMS = ["gpt-3.5-turbo", "gpt-3.5-turbo-instruct", "gpt-4", "gpt-4-turbo"]
_GOOGLE_LLMS = ["gemini-1.0-pro", "gemini-1.5-pro", "gemini-1.5-flash"]
_GROQ_LLMS = ["llama3-70b-8192", "mixtral-8x7b-32768"]
MODEL_NAMES = _OLLAMA_LLMS + _OPENAI_LLMS + _GOOGLE_LLMS + _GROQ_LLMS


def model_names():
    available_models = []
    if os.environ.get("ENV") != "PROD":
        # Include Ollama models if not in production b/c it requires a local Ollama installation
        available_models += _OLLAMA_LLMS

    if os.environ.get("OPENAI_API_KEY"):
        available_models += _OPENAI_LLMS

    if os.environ.get("GOOGLE_API_KEY"):
        available_models += _GOOGLE_LLMS

    if os.environ.get("GROQ_API_KEY"):
        available_models += _GROQ_LLMS

    return available_models


logger = logging.getLogger(__name__)


def init_client(model_name, settings):
    return DspyLlmClient(model_name, settings)


class DspyLlmClient:
    def __init__(self, model_name, settings):
        self.model_name = model_name
        dspy_llm_kwargs = {
            # The default DSPy max_tokens is only 150, which caused issues due to incomplete JSON string output
            "max_tokens": int(os.environ.get("MAX_TOKENS", 1000)),
        } | settings
        logger.info("Creating LLM client '%s' with: %s", self.model_name, dspy_llm_kwargs)

        self.predictor = settings.pop("predictor")
        self.llm = self._create_llm_model(settings)

    def _create_llm_model(self, settings):
        if self.model_name in _OLLAMA_LLMS:
            return dspy.OllamaLocal(model=self.model_name, **settings)
            # Alternative is using OpenAI-compatible API: https://gist.github.com/jrknox1977/78c17e492b5a75ee5bbaf9673aee4641
        if self.model_name in _OPENAI_LLMS:
            if settings.get("respond_with_json", False):
                return dspy.OpenAI(model=self.model_name, **settings, response_format={"type": "json_object"})

            return dspy.OpenAI(model=self.model_name, **settings)
        if self.model_name in _GOOGLE_LLMS:
            return dspy.Google(model=f"models/{self.model_name}", **settings)
        if self.model_name in _GROQ_LLMS:
            api_key = os.environ.get("GROQ_API_KEY")
            return dspy.GROQ(api_key, model=self.model_name, **settings)

        assert False, f"Unknown LLM model: {self.model_name}"

    def generate_reponse(self, message):
        with dspy.context(lm=self.llm):
            return self.predictor(message)
