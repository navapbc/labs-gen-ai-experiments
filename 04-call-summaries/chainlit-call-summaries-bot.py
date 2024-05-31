#!/usr/bin/env chainlit run

import pprint

import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider

from chunking import chunking_ingest
from llm import LLM
from refinement import refinement_ingest
from run import get_transcript, stuffing_summary

OLLAMA_LLMS = ["openhermes", "dolphin-mistral"]
GOOGLE_LLMS = ["gemini-pro", "gemini-flash"]
OPENAI_LLMS = ["gpt-4", "gpt-4o"]
ANTHROPIC_LLMS = ["claude"]
SUMMARIZATION_TECHNIQUE = ["stuffing", "chunking", "refinement"]


@cl.on_chat_start
async def init_chat():
    await cl.Message(
        content="Hi, this is a transcript summarizer, upload a transcript file to summarize it.",
        actions=[
            cl.Action(name="settingsAct", value="chat_settings", label="Show settings"),
            cl.Action(
                name="uploadTranscriptAct",
                value="upload_transcript_file",
                label="Upload transcript file for summarization",
            ),
        ],
    ).send()

    settings = await cl.ChatSettings(
        [
            Select(
                id="model",
                label="LLM Model",
                values=OLLAMA_LLMS + GOOGLE_LLMS + OPENAI_LLMS + ANTHROPIC_LLMS,
                initial_index=0,
            ),
            Select(
                id="summarization_technique",
                label="Choose summarization technique",
                values=SUMMARIZATION_TECHNIQUE,
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
            Switch(id="streaming", label="Stream response tokens", initial=False),
        ]
    ).send()
    cl.user_session.set("settings", settings)
    await init_llm_client_if_needed()


@cl.action_callback("settingsAct")
async def on_click_settings(action: cl.Action):
    settings = cl.user_session.get("settings")
    settings_str = pprint.pformat(settings, indent=4)
    await cl.Message(content=f"{action.value}:\n`{settings_str}`").send()


@cl.on_settings_update
async def update_settings(settings):
    print("Settings updated:", pprint.pformat(settings, indent=4))
    cl.user_session.set("settings", settings)
    await set_llm_model()


async def set_llm_model():
    settings = cl.user_session.get("settings")
    model_name = settings["model"]
    llm_settings = dict((k, settings[k]) for k in ["temperature"] if k in settings)
    msg = cl.Message(
        author="backend",
        content=f"Setting up LLM: {model_name} with `{llm_settings}`...\n",
    )
    client = None
    if model_name in OLLAMA_LLMS:
        client = LLM(client_name="ollama", model_name=model_name, settings=llm_settings)
    elif model_name in GOOGLE_LLMS:
        client = LLM(client_name="gemini", model_name=model_name, settings=llm_settings)
    elif model_name in OPENAI_LLMS:
        client = LLM(client_name="gpt", model_name=model_name, settings=llm_settings)
    elif model_name in ANTHROPIC_LLMS:
        client = LLM(client_name="claude", settings=llm_settings)
    else:
        await cl.Message(content=f"Could not initialize model: {model_name}").send()
        return

    client.init_client()
    cl.user_session.set("client", client)
    await msg.stream_token(f"Done setting up {model_name} LLM")
    await msg.send()


async def init_llm_client_if_needed():
    client = cl.user_session.get("client")
    if not client:
        await set_llm_model()


@cl.action_callback("uploadTranscriptAct")
async def on_click_upload_file_query(action: cl.Action):
    files = None
    # Wait for the user to upload a file
    while files is None:
        files = await cl.AskFileMessage(
            content="Please upload a transcript as a text file.",
            accept=["text/plain", "application/pdf", "application/json"],
            max_size_mb=20,
            timeout=180,
        ).send()
        file = files[0]
        transcript = get_transcript(file_path=file.path)
        settings = cl.user_session.get("settings")
        msg = cl.Message(content=f"Processing `{file.name}`...", disable_feedback=True)
        await msg.send()
        msg.content = f"Processing `{file.name}` completed."
        await msg.update()
        msg.content = "Generating transcript..."
        await msg.update()
        response = await run_summarization_technique(
            technique=settings["summarization_technique"], transcript=transcript
        )
        print(response)
        answer = f"Result:\n{response}"
        await cl.Message(content=answer).send()


async def run_summarization_technique(transcript, technique):
    await init_llm_client_if_needed()
    client = cl.user_session.get("client")
    print(f"client: {client}")
    if technique == "stuffing":
        print("running stuffing")
        return stuffing_summary(transcript=transcript, client=client)
    elif technique == "chunking":
        print("running chunking")
        return chunking_ingest(transcript=transcript, client=client)
    elif technique == "refinement":
        print("running refinement")
        return refinement_ingest(transcript=transcript, client=client)
