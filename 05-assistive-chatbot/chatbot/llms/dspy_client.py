import os

import dspy

CLIENT_NAME = "dspy"

_OLLAMA_LLMS = ["openhermes", "llama2", "llama2:chat", "llama3", "mistral", "mistral:instruct"]
_OPENAI_LLMS = ["gpt-3.5-turbo", "gpt-3.5-turbo-instruct", "gpt-4", "gpt-4-turbo"]
_GOOGLE_LLMS = ["gemini-1.0-pro", "gemini-1.5-pro", "gemini-1.5-flash"]
_GROQ_LLMS = ["llama3-70b-8192", "mixtral-8x7b-32768"]
MODEL_NAMES = _OLLAMA_LLMS + _OPENAI_LLMS + _GOOGLE_LLMS + _GROQ_LLMS


def init_client(model_name, settings):
    return DspyLlmClient(model_name, settings)


class DspyLlmClient:
    def __init__(self, model_name, settings):
        self.llm = self._create_llm_model(model_name, **settings)
        self.predictor = settings["predictor"]

    def _create_llm_model(self, llm_name="openhermes", respond_with_json=False):
        dspy_llm_kwargs = {
            # The default DSPy max_tokens is only 150, which caused issues due to incomplete JSON string output
            "max_tokens": 1000,
        }
        if llm_name in _OLLAMA_LLMS:
            # Alternative using OpenAI-compatible API: https://gist.github.com/jrknox1977/78c17e492b5a75ee5bbaf9673aee4641
            return dspy.OllamaLocal(model=llm_name, **dspy_llm_kwargs)
        elif llm_name in _OPENAI_LLMS:
            if respond_with_json:
                return dspy.OpenAI(model=llm_name, **dspy_llm_kwargs, response_format={"type": "json_object"})
            else:
                return dspy.OpenAI(model=llm_name, **dspy_llm_kwargs)
        elif llm_name in _GOOGLE_LLMS:
            return dspy.Google(model=f"models/{llm_name}", **dspy_llm_kwargs)
        elif llm_name in _GROQ_LLMS:
            api_key = os.environ.get("GROQ_API_KEY")
            return dspy.GROQ(api_key, model=llm_name, **dspy_llm_kwargs)
        else:
            assert False, f"Unknown LLM model: {llm_name}"

    def submit(self, message):
        with dspy.context(lm=self.llm):
            return self.predictor(message)
