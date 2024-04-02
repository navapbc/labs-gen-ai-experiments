import functools
import time
import code
import traceback
from typing import List, Dict, Any
import chainlit as cl
from chainlit.types import ThreadDict

# import readline  # enables Up/Down/History in the console
from langchain_core.runnables import RunnableLambda
from langchain.callbacks.base import BaseCallbackHandler

def timer(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        print(f"(Elapsed time of {func.__name__}: {elapsed_time:0.4f} seconds)")
        return value

    return wrapper_timer


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
        print(f"DEBUG_CHAINLINK {prefix}", x)
        return x

    return RunnableLambda(debug_chainlink)


def print_prompt_templates(chain):
    print("RUNNABLE", chain)  # .json(indent=2))
    if chain.middle:
        print(
            "combine_documents_chain.llm_chain\n",
            chain.middle[0].combine_documents_chain.llm_chain.prompt.template,
        )
        print(
            "combine_documents_chain.document_prompt\n",
            chain.middle[0].combine_documents_chain.document_prompt.template,
        )


class CaptureLlmPromptHandler(BaseCallbackHandler):
    """Prints prompt being sent to an LLM"""

    def __init__(self, printToStdOut=True):
        self.toStdout = printToStdOut

    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        formatted_prompts = "\n".join(prompts).replace("```", "``")
        if self.toStdout:
            print(f"\nPROMPT:\n{formatted_prompts}")
        await cl.Message(
            author="prompt debug",
            content=f"Prompt sent to LLM:\n```\n{formatted_prompts}\n```",
        ).send()


@cl.on_chat_start
async def print_user_sesion():
    # https://docs.chainlit.io/concepts/user-session
    for key in ["id", "env", "chat_settings", "user", "chat_profile", "root_message"]:
        print(key, cl.user_session.get(key))


@cl.on_stop
def on_stop():
    print("The user wants to stop the task!")


# When a user resumes a chat session that was previously disconnected.
# This can only happen if authentication and data persistence are enabled.
@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    print("The user resumed a previous chat session!", thread.keys())


@cl.on_chat_end
def on_chat_end():
    print("The user disconnected!")
