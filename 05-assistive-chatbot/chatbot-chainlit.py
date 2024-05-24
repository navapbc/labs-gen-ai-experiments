#!/usr/bin/env chainlit run -h

import pprint
import dotenv
# import json

# import dotenv
# import dataclasses
# from datetime import date
# import pprint

import chainlit as cl
from chainlit.input_widget import Select, Slider  # , Switch

# import decompose_and_summarize as das
# from decompose_and_summarize import on_question

import llms

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
    dotenv.load_dotenv()
    # settings = das.init()

    elements = [
        cl.Text(name="side-text", display="side", content="Side Text"),
    ]
    await cl.Message("Example of side-text", elements=elements).send()

    settings = await cl.ChatSettings(
        [
            Select(
                id="model",
                label="LLM Model",
                values=llms.available_llms(),
                initial_index=0,
            ),
            Slider(
                id="temperature",
                label="LLM Temperature",
                initial=0.1,
                min=0,
                max=2,
                step=0.1,
            ),
            # TODO: Add streaming capability
            # Switch(id="streaming", label="Stream response tokens", initial=True),
        ]
    ).send()
    cl.user_session.set("settings", settings)


@cl.on_settings_update
async def update_settings(settings):
    print("Settings updated:", pprint.pformat(settings, indent=4))
    cl.user_session.set("settings", settings)
    await set_llm_model()


async def set_llm_model():
    settings = cl.user_session.get("settings")
    llm_name = settings["model"]
    llm_settings = dict((k, settings[k]) for k in ["temperature"] if k in settings)
    msg = cl.Message(
        author="backend",
        content=f"Setting up LLM: {llm_name} with `{llm_settings}`...\n",
    )
    client = llms.init_client(llm_name, llm_settings)

    cl.user_session.set("client", client)
    await msg.stream_token(f"Done setting up {llm_name} LLM")
    await msg.send()


async def init_llm_client_if_needed():
    client = cl.user_session.get("client")
    if not client:
        await set_llm_model()


@cl.on_message
async def message_submitted(message: cl.Message):
    await init_llm_client_if_needed()
    # settings = cl.user_session.get("settings")
    client = cl.user_session.get("client")

    response = client.submit(message.content)
    await cl.Message(content=f"*Response*: {response}").send()

    # generated_results = on_question(message.content)
    # print(json.dumps(dataclasses.asdict(generated_results), indent=2))

    # message_args = format_as_markdown(generated_results)
    await cl.Message(message.content).send()
