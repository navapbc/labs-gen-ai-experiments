#!/usr/bin/env chainlit run

from datetime import date
import pprint

import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider

from llm import ollama_client

OLLAMA_LLMS = ["openhermes", "llama2", "mistral"]
OTHER_LLMS = ["someOtherLLM"]


@cl.on_chat_start
async def init_chat():
    await cl.Message(
        content="Hi! Ask me about Michigan household policies for benefit applications.",
        actions=[
            cl.Action(name="todayAct", value="current_date", label="Today's date"),
            cl.Action(name="settingsAct", value="chat_settings", label="Show settings"),
            cl.Action(name="stepsDemoAct", value="stepsDemo", label="Demo steps"),
            cl.Action(
                name="chooseBetterAct",
                value="chooseBetter",
                label="Demo choosing better response",
            ),
        ],
    ).send()

    # memory = ConversationBufferMemory(memory_key="chat_history", input_key="input", output_key="output", return_messages=True)

    settings = await cl.ChatSettings(
        [
            Select(
                id="model",
                label="LM Model",
                values=OLLAMA_LLMS + OTHER_LLMS,
                initial_index=0,
            ),
            Slider(
                id="temperature",
                label="LLM Temperature",
                initial=0.1,
                min=0,
                max=1,
                step=0.1,
            ),
            Switch(id="streaming", label="Stream response tokens", initial=True),
        ]
    ).send()
    cl.user_session.set("settings", settings)


@cl.action_callback("todayAct")
async def on_click_today(action: cl.Action):
    today = date.today()
    await cl.Message(content=f"{action.value}: Today is {today}").send()


@cl.action_callback("settingsAct")
async def on_click_settings(action: cl.Action):
    settings = cl.user_session.get("settings")
    settings_str = pprint.pformat(settings, indent=4)
    await cl.Message(content=f"{action.value}:\n`{settings_str}`").send()


contentA = """This is text A.
    This is multi-line text.
    It can be used to display longer messages.
    And it can also include markdown formatting.
    E.g. **bold**, *italic*, `code`, [links](https://www.example.com), etc.
"""


@cl.action_callback("stepsDemoAct")
async def on_click_stepsDemo(action: cl.Action):
    async with cl.Step(name="Child step A", disable_feedback=False) as child_step:
        child_step.output = contentA

    async with cl.Step(name="Child step B", disable_feedback=False) as child_step:
        child_step.output = "Hello, this is a text element B."


# Alternative to https://docs.chainlit.io/data-persistence/feedback
@cl.action_callback("chooseBetterAct")
async def on_click_chooseBetter(action: cl.Action):
    await cl.Message(
        content=contentA,
        disable_feedback=True,
        actions=[
            cl.Action(name="choose_response", value="optionA", label="This is better")
        ],
    ).send()
    await cl.Message(
        content="Hello, this is a text B.",
        disable_feedback=True,
        actions=[
            cl.Action(name="choose_response", value="optionB", label="This is better")
        ],
    ).send()


@cl.action_callback("choose_response")
async def on_choose_response(action: cl.Action):
    await cl.Message(
        content=f"User chose: {action.value}", disable_feedback=True
    ).send()


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
    client = None
    if llm_name in OLLAMA_LLMS:
        client = ollama_client(llm_name, settings=llm_settings)
    elif llm_name in OTHER_LLMS:
        await cl.Message(content=f"TODO: Initialize {llm_name} client").send()
        client = None  # TODO: Initialize LLM client here...
    else:
        await cl.Message(content=f"Could not initialize model: {llm_name}").send()
        return

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
    settings = cl.user_session.get("settings")

    # 3 ways to manage history for LLM:
    # 1. Use Chainlit
    # message_history = cl.user_session.get("message_history")
    # message_history.append({"role": "user", "content": message.content})
    # 2. Use LangChain's ConversationBufferMemory
    # 3. Use LlmPrompts lp.register_answer

    # Reminder to use make_async for long running tasks: https://docs.chainlit.io/guides/sync-async#long-running-synchronous-tasks

    if settings["streaming"]:
        await call_llm_async(message)
    else:
        response = call_llm(message)
        await cl.Message(content=f"*Response*: {response}").send()


@cl.step(type="llm", show_input=True)
async def call_llm_async(message: cl.Message):
    client = cl.user_session.get("client")

    botMsg = cl.Message(content="", disable_feedback=False)
    async for chunk in client.astream(message.content):
        await botMsg.stream_token(chunk)
    await botMsg.send()

    response = botMsg.content
    return response


def call_llm(message: cl.Message):
    client = cl.user_session.get("client")
    response = client.invoke(message.content)
    return response
