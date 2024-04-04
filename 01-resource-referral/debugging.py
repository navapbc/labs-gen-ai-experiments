import code
import traceback
# from typing import List, Dict, Any

# import readline  # enables Up/Down/History in the console
from langchain_core.runnables import RunnableLambda
from langchain_core.prompt_values import PromptValue


def stacktrace():
    traceback.print_stack()


def debug_here(local_vars):
    """Usage: debug_here(locals())"""
    variables = globals().copy()
    variables.update(local_vars)
    shell = code.InteractiveConsole(variables)
    shell.interact()


def debug_runnable(prefix: str):
    """Useful to see output/input between Runnables in a LangChain"""

    def debug_chainlink(x):
        print(f"{prefix if prefix else 'DEBUG_CHAINLINK'}")
        if isinstance(x, PromptValue):
            print(x.text)
        else:
            print(type(x), x)
            # debug_here(locals())
        return x

    return RunnableLambda(debug_chainlink)
