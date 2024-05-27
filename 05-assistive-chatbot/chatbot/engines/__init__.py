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
    if not _engines or force:
        _engines.clear()
        found_llm_modules = utils.scan_modules(__package__)
        for _module_name, module in found_llm_modules.items():
            if not hasattr(module, "ENGINE_NAME"):
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


@utils.timer
def create_llm_client(settings):
    llm_name = settings["model"]
    llm_settings = dict((k, settings[k]) for k in ["temperature"] if k in settings)
    client = llms.init_client(llm_name, llm_settings)
    return client
