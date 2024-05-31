import logging
from types import ModuleType
from typing import Dict, Tuple

import chatbot
from chatbot import utils

logger = logging.getLogger(__name__)

_llms: Dict[str, Tuple[ModuleType, str]] = {}


@utils.verbose_timer(logger)
def available_llms():
    return list(_discover_llms()) or ["none found"]


def _discover_llms(force=False):
    if force:
        _llms.clear()
    if not _llms:
        settings = chatbot.initial_settings
        found_modules = utils.scan_modules(__package__)
        for module_name, module in found_modules.items():
            if not module or ignore(module_name):
                logger.debug("Skipping module: %s", module_name)
                continue
            if hasattr(module, "requirements_satisfied") and not module.requirements_satisfied(settings):
                logger.debug("Module requirements not satisfied; skipping: %s", module_name)
                continue
            client_name = module.CLIENT_NAME or module_name
            if hasattr(module, "model_names"):
                model_names = module.model_names(settings)
            else:
                model_names = module.MODEL_NAMES

            for llm_name in model_names:
                qualified_name = qualified_llm_name(client_name, llm_name)
                _llms[qualified_name] = (module, llm_name)
    return _llms


def qualified_llm_name(client_name, model_name):
    return f"{client_name} :: {model_name}"


def ignore(_module_name):
    # if module_name.startswith("dspy ::"):
    #     # DSPy client code is not yet ready for use
    #     return True
    return False


## Factory functions


def init_client(qualified_name, settings=None):
    """Initialize a specific LLM client based on the qualified_name.
    :param qualified_name: str or Tuple[client_name, model_name]
    """
    _discover_llms()
    if isinstance(qualified_name, Tuple):
        qualified_name = qualified_llm_name(qualified_name[0], qualified_name[1])
    module, llm_name = _llms[qualified_name]
    return module.init_client(llm_name, settings or {})
