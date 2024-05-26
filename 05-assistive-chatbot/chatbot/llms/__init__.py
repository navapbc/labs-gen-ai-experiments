import importlib
import logging
from types import ModuleType
from typing import Dict, Tuple

from chatbot import utils

logger = logging.getLogger(__name__)

_llms: Dict[str, Tuple[ModuleType, str]] = {}


@utils.verbose_timer(logger)
def available_llms():
    return list(_discover_llms()) or ["none found"]


def _discover_llms(force=False):
    if not _llms or force:
        _llms.clear()
        namespace = importlib.import_module(__package__)
        found_modules = utils.scan_modules(namespace)
        for module_name, module in found_modules.items():
            if not module or ignore(module_name):
                logger.debug("Skipping module: %s", module_name)
                continue
            client_name = module.CLIENT_NAME or module_name
            for llm_name in module.MODEL_NAMES or []:
                qualified_llm_name = f"{client_name} :: {llm_name}"
                _llms[qualified_llm_name] = (module, llm_name)
    return _llms


def ignore(module_name):
    if module_name.startswith("dspy ::"):
        return True
    return False


## Factory functions


def init_client(model_name, settings=None):
    _discover_llms()
    module, llm_name = _llms[model_name]
    return module.init_client(llm_name, settings)
