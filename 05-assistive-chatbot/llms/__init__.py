import importlib
import logging
from types import ModuleType
from typing import Dict, Tuple

import utils

logger = logging.getLogger(__name__)

llm_modules: Dict[str, Tuple[ModuleType, str]] = {}


@utils.verbose_timer(logger)
def available_llms():
    return list(discover_llms(True).keys()) or ["none found"]


def discover_llms(force=False):
    if not llm_modules or force:
        llm_modules.clear()
        namespace = importlib.import_module(__package__)
        found_llm_modules = utils.scan_modules(namespace)
        for module_name, module in found_llm_modules.items():
            client_name = module.CLIENT_NAME or module_name
            for llm_name in module.MODEL_NAMES or []:
                qualified_llm_name = f"{client_name} :: {llm_name}"
                llm_modules[qualified_llm_name] = (module, llm_name)
    return llm_modules


def init_client(model_name, settings=None):
    module, llm_name = llm_modules[model_name]
    return module.init_client(llm_name, settings)
