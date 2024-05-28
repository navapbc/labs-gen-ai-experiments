import logging
import os

import dotenv

from chatbot import engines, llms, utils

# TODO
# - add exception handling
# - add unit tests


## Initialize logging


def configure_logging():
    log_format = os.environ.get("LOG_FORMAT", "%(relativeCreated)6d - %(name)-24s - %(levelname)-5s - %(message)s")
    logging.basicConfig(format=log_format)

    log_level = os.environ.get("CHATBOT_LOG_LEVEL", "WARN")
    logging.getLogger("chatbot").setLevel(getattr(logging, log_level))
    logging.info("Configured logging level: %s", log_level)


dotenv.load_dotenv()
configure_logging()

logger = logging.getLogger(__name__)


## Initialize settings


@utils.verbose_timer(logger)
def _init_settings():
    return {
        "enable_api": is_true(os.environ.get("ENABLE_CHATBOT_API", "False")),
        "chat_engine": os.environ.get("CHAT_ENGINE", "Direct"),
        "model": os.environ.get("LLM_MODEL_NAME", "mock :: llm"),
        "temperature": float(os.environ.get("LLM_TEMPERATURE", 0.1)),
    }


def is_true(string):
    return string.lower() not in ["false", "f", "no", "n"]


initial_settings = _init_settings()


@utils.verbose_timer(logger)
def validate_settings(settings):
    chat_engine = settings["chat_engine"]
    if chat_engine not in engines._discover_chat_engines():
        return f"Unknown chat_engine: '{chat_engine}'"

    model_name = settings["model"]
    if model_name not in llms._discover_llms():
        return f"Unknown model: '{model_name}'"

    # PLACEHOLDER: Validate other settings

    return None


## Chat Engine


@utils.timer
def create_chat_engine(settings):
    return engines.create_engine(settings["chat_engine"], settings)
