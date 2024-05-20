#!/usr/bin/env chainlit run

import json

# import dotenv
import dataclasses
# from datetime import date
# import pprint

import chainlit as cl
# from chainlit.input_widget import Select, Switch, Slider

# import decompose_and_summarize as das
from decompose_and_summarize import on_question


@cl.on_chat_start
async def init_chat():
    # settings = das.init()
    html = """
Derived Questions
<details>
  <summary>Epcot Center</summary>
  <p>Epcot is a theme park at Walt Disney World Resort featuring exciting attractions, international pavilions, award-winning fireworks and seasonal special events.</p>
</details>
Derived Questions"""
    await cl.Message(
        content=f"## Some content\n{html}",
        elements=[cl.Text(name="Derived Questions", content="## SIDE", display="side")],
    ).send()

    elements = [
        cl.Text(name="side-text", display="side", content="Side Text"),
        cl.Text(name="page-text", display="page", content="Page Text"),
    ]
    await cl.Message("hello side-text and page-text", elements=elements).send()

    pass


@cl.on_message
async def message_submitted(message: cl.Message):
    generated_results = on_question(message.content)
    print(json.dumps(dataclasses.asdict(generated_results), indent=2))

    message_args = format_as_markdown(generated_results)
    # await cl.Message(**message_args).send()
    await cl.Message(content=message_args["content"], elements=message_args["elements"]).send()
    # await cl.Message(content= message_args["content"], elements=[cl.Text(content="SIDE", display="inline")]).send()


def format_as_markdown(gen_results):
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
