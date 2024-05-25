import importlib
import logging
from types import ModuleType
from typing import Dict

import utils

logger = logging.getLogger(__name__)

engines: Dict[str, ModuleType] = {}


@utils.timer
def create(engine_name, settings=None):
    return engines[engine_name].init_engine(settings)


@utils.verbose_timer(logger)
def discover_chat_engines():
    namespace = importlib.import_module(__package__)
    found_llm_modules = utils.scan_modules(namespace)
    for _module_name, module in found_llm_modules.items():
        if not hasattr(module, "ENGINE_NAME"):
            continue
        engine_name = module.ENGINE_NAME
        engines[engine_name] = module
    return engines


discover_chat_engines()
