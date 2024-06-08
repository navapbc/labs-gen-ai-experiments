import importlib
import logging
import os
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
        ENGINE_MODULES = os.environ.get("ENGINE_MODULES", "").split(",")
        engine_modules = {name: importlib.import_module(f"chatbot.engines.{name}") for name in ENGINE_MODULES if name}
        if not engine_modules:
            engine_modules = utils.scan_modules(__package__)

        settings = chatbot.initial_settings
        for module_name, module in engine_modules.items():
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

# Settings that are specific to LLMs and should be passed onto the LLM client
LLM_SETTING_KEYS = ["temperature"]


@utils.timer
def create_llm_client(settings):
    llm_name = settings["model"]
    remaining_settings = {k: settings[k] for k in settings if k in LLM_SETTING_KEYS}
    client = llms.init_client(llm_name, remaining_settings)
    return client
