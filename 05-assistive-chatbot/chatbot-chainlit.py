#!/usr/bin/env chainlit run -h

import logging
import pprint

import chainlit as cl
from chainlit.input_widget import Select, Slider  # , Switch
from chainlit.types import ThreadDict

import chatbot
from chatbot import engines, llms, utils

logger = logging.getLogger(f"chatbot.{__name__}")

if chatbot.initial_settings["enable_api"]:
    import chatbot_api

    logger.info("Chatbot API loaded: %s", chatbot_api.__name__)


@cl.on_chat_start
async def init_chat():
    elements = [
        cl.Text(name="side-text", display="side", content="Side Text"),
    ]
    await cl.Message("Example of side-text", elements=elements).send()

    # https://docs.chainlit.io/api-reference/chat-settings
    chat_settings = cl.ChatSettings(
        [
            Select(
                id="chat_engine",
                label="Chat Mode",
                values=engines.available_engines(),
                initial_value=chatbot.initial_settings["chat_engine"],
            ),
            Select(
                id="model",
                label="LLM Model",
                values=llms.available_llms(),
                initial_value=chatbot.initial_settings["model"],
            ),
            Slider(
                id="temperature",
                label="LLM Temperature",
                initial=chatbot.initial_settings["temperature"],
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


@cl.on_settings_update
async def update_settings(settings):
    logger.info("Settings updated: %s", pprint.pformat(settings, indent=4))
    cl.user_session.set("settings", settings)
    await apply_settings()


@utils.timer
async def apply_settings():
    settings = cl.user_session.get("settings")
    await create_llm_client(settings)

    # PLACEHOLDER: Apply other settings

    error = chatbot.validate_settings(settings)
    if error:
        await cl.Message(author="backend", content=f"! Validation error: {error}").send()
    else:
        cl.user_session.set("settings_applied", True)
    return settings


async def create_llm_client(settings):
    msg = cl.Message(author="backend", content=f"Setting up LLM: {settings['model']} ...\n")

    cl.user_session.set("chat_engine", chatbot.create_chat_engine(settings))
    await msg.stream_token("Done setting up LLM")
    await msg.send()


@cl.on_message
async def message_submitted(message: cl.Message):
    if not cl.user_session.get("settings_applied", False):
        await apply_settings()
        if not cl.user_session.get("settings_applied", False):
            return

    # settings = cl.user_session.get("settings")

    chat_engine = cl.user_session.get("chat_engine")
    response = chat_engine.get_response(message.content)

    await cl.Message(content=f"*Response*: {response}").send()

    # generated_results = on_question(message.content)
    # print(json.dumps(dataclasses.asdict(generated_results), indent=2))

    # message_args = format_as_markdown(generated_results)
    await cl.Message(message.content).send()


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
