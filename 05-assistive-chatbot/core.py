import os
import dotenv

import llms
import utils

import logging

logging.basicConfig(level=logging.WARN, format="%(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def is_true(string):
    return string.lower() not in ["false", "f", "no", "n"]


dotenv.load_dotenv()
# Lower number results in less verbose output


@utils.verbose_timer(logger)
def init_settings():
    return {
        "enable_api": is_true(os.environ.get("ENABLE_CHATBOT_API", "False")),
        "model": os.environ.get("LLM_MODEL_NAME", "mock :: llm"),
        "temperature": float(os.environ.get("LLM_TEMPERATURE", 0.1)),
    }


initial_settings = init_settings()


@utils.timer
def validate_settings(settings):
    model_name = settings["model"]
    if model_name not in llms.available_llms():
        return f"Unknown model: '{model_name}'"

    # PLACEHOLDER: Validate other settings

    return None


@utils.timer
def create_llm_client(settings):
    llm_name = settings["model"]
    llm_settings = dict((k, settings[k]) for k in ["temperature"] if k in settings)
    client = llms.init_client(llm_name, llm_settings)
    return client
