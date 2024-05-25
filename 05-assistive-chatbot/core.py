import logging
import os

import dotenv

import chat_engines
import llms
import utils

log_format = os.environ.get("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging.basicConfig(level=logging.DEBUG, format=log_format)

logger = logging.getLogger(__name__)


def is_true(string):
    return string.lower() not in ["false", "f", "no", "n"]


dotenv.load_dotenv()
# Lower number results in less verbose output


@utils.verbose_timer(logger)
def init_settings():
    return {
        "enable_api": is_true(os.environ.get("ENABLE_CHATBOT_API", "False")),
        "chat_engine": os.environ.get("CHAT_ENGINE", "Direct"),
        "model": os.environ.get("LLM_MODEL_NAME", "mock :: llm"),
        "temperature": float(os.environ.get("LLM_TEMPERATURE", 0.1)),
    }


initial_settings = init_settings()


@utils.verbose_timer(logger)
def validate_settings(settings):
    model_name = settings["model"]
    if model_name not in llms.available_llms():
        return f"Unknown model: '{model_name}'"

    # PLACEHOLDER: Validate other settings

    return None


@utils.timer
def create_chat_engine(settings):
    return chat_engines.create(settings["chat_engine"], settings)
