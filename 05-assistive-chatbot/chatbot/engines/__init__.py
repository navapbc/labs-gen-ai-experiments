import logging
from types import ModuleType
from typing import Dict

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
        found_llm_modules = utils.scan_modules(__package__)
        for module_name, module in found_llm_modules.items():
            if not hasattr(module, "ENGINE_NAME"):
                logger.debug("Skipping module without an ENGINE_NAME: %s", module_name)
                continue
            if hasattr(module, "requirements_satisfied") and not module.requirements_satisfied():
                logger.debug("Engine requirements not satisfied; skipping: %s", module_name)
                continue
            engine_name = module.ENGINE_NAME
            _engines[engine_name] = module
    return _engines


## Factory functions


@utils.timer
def create(engine_name, settings=None):
    _discover_chat_engines()
    return _engines[engine_name].init_engine(settings)


## Utility functions

CHATBOT_SETTING_KEYS = ["enable_api", "chat_engine", "model"]

@utils.timer
def create_llm_client(settings):
    llm_name = settings["model"]
    # llm_settings = dict((k, settings[k]) for k in ["temperature"] if k in settings)
    remaining_settings = { k: settings[k] for k in settings if k not in CHATBOT_SETTING_KEYS }
    client = llms.init_client(llm_name, remaining_settings)
    return client
