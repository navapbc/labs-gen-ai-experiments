from typing import Dict, Tuple
from types import ModuleType

import importlib
import pkgutil


llm_modules: Dict[str, Tuple[ModuleType, str]] = {}


def available_llms():
    return list(discover_llms().keys()) or ["none found"]


SELF_NAMESPACE = importlib.import_module(__package__)


def discover_llms(force=False):
    if not llm_modules or force:
        llm_modules.clear()
        found_llm_modules = [name for _, name, _ in iter_modules_in_namespace(SELF_NAMESPACE)]
        print("Found LLM modules:", found_llm_modules)
        for module_name in found_llm_modules:
            module = importlib.import_module(module_name)
            client_name = getattr(module, "CLIENT_NAME", module_name)
            for llm_name in getattr(module, "MODEL_NAMES", []):
                qualified_llm_name = f"{client_name} :: {llm_name}"
                llm_modules[qualified_llm_name] = (module, llm_name)
    return llm_modules


# From https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/#using-namespace-packages
def iter_modules_in_namespace(ns_pkg):
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")


def init_client(model_name, settings=None):
    module, llm_name = llm_modules[model_name]
    return module.init_client(llm_name, settings)
