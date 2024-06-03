import logging
from types import ModuleType
from typing import Dict

import chatbot
from chatbot import llms, utils

logger = logging.getLogger(__name__)

_engines: Dict[str, ModuleType] = {}


@utils.verbose_timer(logger)
def available_engines():
    return list(_discover_chat_engines().keys()) or ["none found"]


def _discover_chat_engines(force=False):
    if force:
        _engines.clear()
    if not _engines:
        settings = chatbot.initial_settings
        found_llm_modules = utils.scan_modules(__package__)
        for module_name, module in found_llm_modules.items():
            if not hasattr(module, "ENGINE_NAME"):
                logger.debug("Skipping module without an ENGINE_NAME: %s", module_name)
                continue
            if hasattr(module, "requirements_satisfied") and not module.requirements_satisfied(settings):
                logger.debug("Engine requirements not satisfied; skipping: %s", module_name)
                continue
            engine_name = module.ENGINE_NAME
            _engines[engine_name] = module
    return _engines


## Factory functions


@utils.timer
def create_engine(engine_name, settings=None):
    _discover_chat_engines()
    return _engines[engine_name].init_engine(settings)


## Utility functions

# Settings that are specific to our chatbot and shouldn't be passed onto the LLM client
CHATBOT_SETTING_KEYS = ["env", "enable_api", "chat_engine", "model", "model2", "temperature2", "retrieve_k"]


@utils.timer
def create_llm_client(settings):
    llm_name = settings["model"]
    remaining_settings = {k: settings[k] for k in settings if k not in CHATBOT_SETTING_KEYS}
    client = llms.init_client(llm_name, remaining_settings)
    return client
