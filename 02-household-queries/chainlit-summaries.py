#!/usr/bin/env chainlit run

import json
import dotenv
import dataclasses
from datetime import date
import pprint

import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider

import decompose_and_summarize as das
from decompose_and_summarize import on_question


@cl.on_chat_start
async def init_chat():
    # settings = das.init()
    pass


@cl.on_message
async def message_submitted(message: cl.Message):
    generated_results = on_question(message.content)
    print(json.dumps(dataclasses.asdict(generated_results), indent=2))

    await cl.Message(format_as_markdown(generated_results)).send()


def format_as_markdown(gen_results):
    resp = ["", f"## Q: {gen_results.question}", "### Derived Questions"]

    for dq in gen_results.derived_questions:
        resp.append(f"1. {dq.derived_question}")

    resp.append("### Guru cards")
    for card in gen_results.cards:
        if card.summary:
            resp += [f"#### {card.card_title}", f"Summary: {card.summary}", ""]
            resp += [f"\n.\n> {q}" for q in card.quotes]

    return "\n".join(resp)
