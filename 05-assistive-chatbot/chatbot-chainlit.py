#!/usr/bin/env chainlit run

# import json

# import dotenv
# import dataclasses
# from datetime import date
# import pprint

import chainlit as cl
# from chainlit.input_widget import Select, Switch, Slider

# import decompose_and_summarize as das
# from decompose_and_summarize import on_question

# TODO
# - set up Chainlit Settings
# - allow user to choose LLM
# - add exception handling
# - add unit tests

@cl.on_chat_start
async def init_chat():
    # settings = das.init()

    elements = [
        cl.Text(name="side-text", display="side", content="Side Text"),
        cl.Text(name="page-text", display="page", content="Page Text"),
    ]
    await cl.Message("hello side-text and page-text", elements=elements).send()


@cl.on_message
async def message_submitted(message: cl.Message):
    # generated_results = on_question(message.content)
    # print(json.dumps(dataclasses.asdict(generated_results), indent=2))

    # message_args = format_as_markdown(generated_results)
    await cl.Message(message.content).send()
