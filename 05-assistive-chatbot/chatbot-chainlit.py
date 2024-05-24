#!/usr/bin/env chainlit run -h

import pprint
# import json

# import dotenv
# import dataclasses
# from datetime import date
# import pprint

import chainlit as cl
from chainlit.input_widget import Select, Slider  # , Switch

# import decompose_and_summarize as das
# from decompose_and_summarize import on_question

import core
import llms

import chatbot_api

print("Chatbot API loaded", chatbot_api)

# TODO
# - set up Chainlit Settings
# - allow user to choose LLM
# - add exception handling
# - add unit tests


# TODO: Add a reset button
async def reset():
    llms.llm_modules.clear()
    # cl.user_session.clear()


@cl.on_chat_start
async def init_chat():
    # settings = das.init()

    elements = [
        cl.Text(name="side-text", display="side", content="Side Text"),
    ]
    await cl.Message("Example of side-text", elements=elements).send()

    # https://docs.chainlit.io/api-reference/chat-settings
    chat_settings = cl.ChatSettings(
        [
            Select(
                id="model",
                label="LLM Model",
                values=llms.available_llms(),
                initial_value=core.initial_settings["model"],
            ),
            Slider(
                id="temperature",
                label="LLM Temperature",
                initial=0.1,
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
    error = core.validate_settings(settings)
    if error:
        assert False, f"Validation error: {error}"


@cl.on_settings_update
async def update_settings(settings):
    print("Settings updated:", pprint.pformat(settings, indent=4))
    cl.user_session.set("settings", settings)
    await apply_settings()


async def apply_settings():
    settings = cl.user_session.get("settings")
    await create_llm_client(settings)

    # PLACEHOLDER: Apply other settings

    error = core.validate_settings(settings)
    if error:
        await cl.Message(author="backend", content=f"! Validation error: {error}").send()
    else:
        cl.user_session.set("settings_applied", True)


async def create_llm_client(settings):
    llm_name = settings["model"]
    llm_settings = dict((k, settings[k]) for k in ["temperature"] if k in settings)
    msg = cl.Message(
        author="backend",
        content=f"Setting up LLM: {llm_name} with `{llm_settings}`...\n",
    )

    client = core.create_llm_client(settings)

    cl.user_session.set("client", client)
    await msg.stream_token(f"Done setting up {llm_name} LLM")
    await msg.send()


@cl.on_message
async def message_submitted(message: cl.Message):
    if not cl.user_session.get("settings_applied", False):
        await apply_settings()
        if not cl.user_session.get("settings_applied", False):
            return

    # settings = cl.user_session.get("settings")
    client = cl.user_session.get("client")

    response = client.submit(message.content)
    await cl.Message(content=f"*Response*: {response}").send()

    # generated_results = on_question(message.content)
    # print(json.dumps(dataclasses.asdict(generated_results), indent=2))

    # message_args = format_as_markdown(generated_results)
    await cl.Message(message.content).send()
