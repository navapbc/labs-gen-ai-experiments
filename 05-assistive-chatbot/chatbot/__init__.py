import logging
import os
from datetime import date

import dotenv

from chatbot import engines, llms, utils

# TODO
# - add exception handling
# - add unit tests


## Set default environment variables


# Opt out of telemetry -- https://docs.trychroma.com/telemetry
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

# Used by SentenceTransformerEmbeddings and HuggingFaceEmbeddings
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", "./.sentence-transformers-cache")

# Disable DSPy cache to get different responses for retry attempts
# Set to true to enable caching for faster responses and optimizing prompts using DSPy
os.environ.setdefault("DSP_CACHEBOOL", "false")

os.environ.setdefault("BUILD_DATE", str(date.today()))


## Initialize logging


def configure_logging():
    log_format = os.environ.get("LOG_FORMAT", "%(relativeCreated)6d - %(name)-24s - %(levelname)-5s - %(message)s")
    logging.basicConfig(format=log_format)

    log_level = os.environ.get("CHATBOT_LOG_LEVEL", "WARN")
    logging.getLogger("chatbot").setLevel(getattr(logging, log_level))
    logging.info("Configured logging level: %s", log_level)


env = os.environ.get("ENV", "DEV")
print(f"Loading .env-{env}")
dotenv.load_dotenv(f".env-{env}")
dotenv.load_dotenv()
configure_logging()
logger = logging.getLogger(__name__)
logger.info("Build date: %s", os.environ.get("BUILD_DATE"))

if env == "PROD":
    # https://www.uvicorn.org/settings/#production
    # https://sentry.io/answers/number-of-uvicorn-workers-needed-in-production/
    # Too many workers will use more resources, which slows down all operations
    os.environ.setdefault("WEB_CONCURRENCY", "2")


## Initialize settings


@utils.verbose_timer(logger)
def _init_settings():
    # Remember to update ChatSettings in chatbot-chainlit.py when adding new settings
    # and update chatbot/engines/__init.py:CHATBOT_SETTING_KEYS
    return {
        "env": env,
        "enable_api": is_true(os.environ.get("ENABLE_CHATBOT_API", "False")),
        "chat_engine": os.environ.get("CHAT_ENGINE", "Direct"),
        "model": os.environ.get("LLM_MODEL_NAME", "mock :: llm"),
        "temperature": float(os.environ.get("LLM_TEMPERATURE", 0.1)),
        "retrieve_k": int(os.environ.get("RETRIEVE_K", 4)),
        # Used by SummariesChatEngine
        "model2": os.environ.get("LLM_MODEL_NAME_2", os.environ.get("LLM_MODEL_NAME", "mock :: llm")),
        "temperature2": float(os.environ.get("LLM_TEMPERATURE2", 0.1)),
    }


def is_true(string):
    return string.lower() not in ["false", "f", "no", "n"]


initial_settings = _init_settings()


def reset():
    configure_logging()
    engines._engines.clear()
    llms._llms.clear()
    global initial_settings
    initial_settings = _init_settings()


@utils.verbose_timer(logger)
def validate_settings(settings):
    chat_engine = settings["chat_engine"]
    if chat_engine not in engines._discover_chat_engines():
        return f"Unknown chat_engine: '{chat_engine}'"

    for setting_name in ["model", "model2"]:
        model_name = settings[setting_name]
        if model_name not in llms._discover_llms():
            return f"Unknown {setting_name}: '{model_name}'"

        if chat_engine.startswith("Summaries") and "instruct" not in model_name:
            # TODO: also send to user
            logger.warning("For the %s chat engine, an `*instruct` model is recommended", chat_engine)

    # PLACEHOLDER: Validate other settings

    return None


## Chat Engine


@utils.timer
def create_chat_engine(settings):
    return engines.create_engine(settings["chat_engine"], settings)
