#!/usr/bin/env chainlit run -h

"""
Chainlit-based chatbot, providing a web user interface for the selected chat engine and settings.
See README.md for instructions to enable user feedback.
"""

import logging
import os
import pprint
import socket

import chainlit as cl
from chainlit.input_widget import Select, Slider  # , Switch
from chainlit.types import ThreadDict

import chatbot
from chatbot import engines, llms, utils
from chatbot.engines import v2_household_engine

logger = logging.getLogger(f"chatbot.{__name__}")

if utils.is_env_var_true("ENABLE_CHATBOT_API", False):
    import chatbot_api

    logger.info("Chatbot API loaded: %s", chatbot_api.__name__)

## TODO: Enable users to log in so that they can be distinguished in GetLiteralAI feedback logs


@cl.on_chat_start
async def init_chat():
    logger.debug("init_chat")
    git_sha = os.environ.get("GIT_SHA", "")
    build_date = os.environ.get("BUILD_DATE", "unknown")
    initial_settings = chatbot.create_init_settings()
    service_name = os.environ.get("SERVICE_NAME", "n/a")
    metadata = {
        **initial_settings,
        "build_date": build_date,
        "git_sha": git_sha,
        "service_name": service_name,
        "hostname": socket.gethostname(),
    }

    await cl.Message(
        metadata=metadata,
        disable_feedback=True,
        content=f"Welcome to the Assistive Chat prototype (built {build_date})",
    ).send()

    available_llms = llms.available_llms()
    # https://docs.chainlit.io/api-reference/chat-settings
    chat_settings = cl.ChatSettings(
        [
            Select(
                id="chat_engine",
                label="Chat Mode",
                values=engines.available_engines(),
                initial_value=initial_settings["chat_engine"],
            ),
            Select(
                id="model",
                label="Primary LLM Model",
                values=available_llms,
                initial_value=initial_settings["model"],
            ),
            Slider(
                id="temperature",
                label="Temperature for primary LLM",
                initial=initial_settings["temperature"],
                min=0,
                max=2,
                step=0.1,
            ),
            Slider(
                id="retrieve_k",
                label="Guru cards to retrieve",
                initial=initial_settings["retrieve_k"],
                min=1,
                max=10,
                step=1,
            ),
            Select(
                id="model2",
                label="LLM Model for summarizer",
                values=available_llms,
                initial_value=initial_settings["model2"],
            ),
            Slider(
                id="temperature2",
                label="Temperature for summarizer",
                initial=initial_settings["temperature2"],
                min=0,
                max=2,
                step=0.1,
            ),
            # TODO: Add LLM response streaming capability
            # Switch(id="streaming", label="Stream response tokens", initial=True),
        ]
    )
    settings = await chat_settings.send()
    cl.user_session.set("settings", settings)
    error = chatbot.validate_settings(settings)
    if error:
        assert False, f"Validation error: {error}"

    preload_chat_engine_default = "ENGINE_MODULES" in os.environ and "LLM_MODULES" in os.environ
    if utils.is_env_var_true("PRELOAD_CHAT_ENGINE", preload_chat_engine_default):
        logger.info("Preloading chat engine")
        await apply_settings()


@cl.on_settings_update
async def update_settings(settings):
    logger.info("Settings updated: %s", pprint.pformat(settings, indent=4))
    cl.user_session.set("settings", settings)
    await apply_settings()


@utils.timer
async def apply_settings():
    # reset settings_applied flag in case of failure during apply_settings
    cl.user_session.set("settings_applied", False)

    settings = cl.user_session.get("settings")
    await create_chat_engine(settings)

    error = chatbot.validate_settings(settings)
    if error:
        await cl.Message(author="backend", metadata=settings, content=f"! Validation error: {error}").send()
    else:
        cl.user_session.set("settings_applied", True)
    return settings


async def create_chat_engine(settings):
    async with cl.Step(name="system") as step:
        step.streaming = True
        step.metadata = settings
        step.output = f"Setting up chat engine: {settings['chat_engine']} ...\n"

        cl.user_session.set("chat_engine", chatbot.create_chat_engine(settings))
        await step.stream_token("Done setting up chat engine")
        await step.send()


@cl.on_message
async def message_submitted(message: cl.Message):
    if not cl.user_session.get("settings_applied", False):
        await apply_settings()
        # If settings not applied successfully, don't proceed
        if not cl.user_session.get("settings_applied", False):
            return

    # If the latest message content is empty, Chainlit will display a loader while the content remains empty.
    # https://docs.chainlit.io/concepts/message#trick-display-a-loader-while-waiting-for-a-response
    response_msg = cl.Message(content="")
    await response_msg.send()

    chat_engine = cl.user_session.get("chat_engine")
    response = chat_engine.gen_response(message.content)

    if isinstance(response, v2_household_engine.GenerationResults):
        format_v2_results_as_markdown(response, response_msg)
    elif isinstance(response, str):
        response_msg.content = response
    elif isinstance(response, dict):
        await handle_response_dict(message, response, response_msg)
    else:
        response_msg.content = f"*Response*: {response}"

    await response_msg.update()


async def handle_response_dict(message, response, response_msg):
    error_msg = response.pop("errorMsg", None)
    system_msg = response.pop("systemMsg", None)

    if "content" in response:
        response_msg_args = convert_to_message_args(response)
        response_msg.content = response_msg_args["content"]
        response_msg.metadata = response_msg_args.get("metadata", {})
    else:
        response_msg.content = f"*Response Object*: {response}"

    if error_msg:
        async with cl.Step(name="error", parent_id=message.id) as step:
            error_msg_args = convert_to_message_args(error_msg)
            step.is_error = True
            step.output = error_msg_args["content"]

    if system_msg:
        async with cl.Step(name="system", parent_id=message.id) as step:
            system_msg_args = convert_to_message_args(system_msg)
            step.output = error_msg_args["content"]
            if "metadata" in system_msg_args:
                step.metadata = system_msg_args["metadata"]


def convert_to_message_args(response_obj: str | dict):
    if isinstance(response_obj, str):
        return {"content": response_obj}
    if isinstance(response_obj, dict):
        return response_obj


def format_v2_results_as_markdown(gen_results, response_msg):
    resp = ["", f"## Q: {gen_results.question}"]

    dq_resp = ["<details><summary>Derived Questions</summary>", ""]
    for dq in gen_results.derived_questions:
        dq_resp.append(f"- {dq.derived_question}")
    dq_resp += ["</details>", ""]

    cards_resp = []
    for i, card in enumerate(gen_results.cards, 1):
        if card.summary:
            cards_resp += [
                f"<details><summary>{i}. <a href='https://link/to/guru_card'>{card.card_title}</a></summary>",
                "",
                f"   Summary: {card.summary}",
                "",
            ]
            indented_quotes = [q.strip().replace("\n", "\n   ") for q in card.quotes]
            cards_resp += [f"\n   Quote:\n   ```\n   {q}\n   ```" for q in indented_quotes]
            cards_resp += ["</details>", ""]

    response_msg.content = "\n".join(resp + dq_resp + cards_resp)
    response_msg.elements = [
        # Example of how to use cl.Text with different display parameters -- it's not intuitive
        # The name argument must exist in the message content so that a link can be created.
        # cl.Text(name="Derived Questions", content="\n".join(dq_resp), display="side"),
        # cl.Text(name="Guru Cards", content="\n".join(cards_resp), display="inline")
    ]


@cl.on_stop
def on_stop():
    logger.debug("The user wants to stop the task!")


# When a user resumes a chat session that was previously disconnected.
# This can only happen if authentication and data persistence are enabled.
@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    logger.debug("The user resumed a previous chat session! %s", thread.keys())


@cl.on_chat_end
def on_chat_end():
    logger.debug("The user disconnected!")
