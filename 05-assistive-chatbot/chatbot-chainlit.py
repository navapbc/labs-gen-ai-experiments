#!/usr/bin/env chainlit run -h

"""
Chainlit-based chatbot, providing a web user interface for the selected chat engine and settings.
See README.md for instructions to enable user feedback.
"""

import logging
import pprint

import chainlit as cl
from chainlit.input_widget import Select, Slider  # , Switch
from chainlit.types import ThreadDict

import chatbot
from chatbot import engines, llms, utils
from chatbot.engines import v2_household_engine

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
            Slider(
                id="retrieve_k",
                label="Guru cards to retrieve",
                initial=chatbot.initial_settings["retrieve_k"],
                min=1,
                max=10,
                step=1,
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

    chat_engine = cl.user_session.get("chat_engine")
    response = chat_engine.gen_response(message.content)

    if isinstance(response, v2_household_engine.GenerationResults):
        message_args = format_v2_results_as_markdown(response)
        await cl.Message(content=message_args["content"], elements=message_args["elements"]).send()
    else:
        await cl.Message(content=f"*Response*: {response}").send()


def format_v2_results_as_markdown(gen_results):
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

    return {
        "content": "\n".join(resp + dq_resp + cards_resp),
        "elements": [
            # cl.Text(name="Derived Questions", content="\n".join(dq_resp), display="side"),
            # cl.Text(name="Guru Cards", content="\n".join(cards_resp), display="inline")
        ],
    }


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
