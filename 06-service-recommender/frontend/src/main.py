# https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps#build-a-simple-chatbot-gui-with-streaming
import logging
import json
import os
import re
import time
from pprint import pformat

import requests

# TODO: Try Streamlit alternatives:
#   https://www.assistant-ui.com/examples
#   https://docs.nlkit.com/nlux/examples/react-js-ai-assistant
#   https://fredrikoseberg.github.io/react-chatbot-kit-docs/
import streamlit as st


logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO
)

st.title("Simple chat")

HAYHOOKS_URL = os.environ.get("HAYHOOKS_URL", "http://localhost:1416")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Query available pipelines from the Hayhooks API
if "pipelines" not in st.session_state:
    models_resp = requests.get(f"{HAYHOOKS_URL}/models")
    if models_resp.ok:
        st.session_state.pipelines = [
            model["name"] for model in models_resp.json()["data"]
        ]
        logger.info("Available pipelines: %s", st.session_state.pipelines)
    else:
        logger.error("Failed to fetch models from Hayhooks API: %s", models_resp.text)
        st.session_state.pipelines = []


with st.sidebar:
    st.write("[Phoenix UI](http://localhost:6006)")
    st.write("[Hayhooks API](http://localhost:1416/docs)")
    pipeline = st.selectbox(
        "Hayhook pipeline to use",
        st.session_state.pipelines,
    )
    stream_response = st.checkbox("Stream response?", value=True)

# Display chat messages from history on st.rerun()
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("How may I help?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})


def simulated_response_generator(question):
    # Send POST request to the backend
    payload = {"question": question}
    url = f"{HAYHOOKS_URL}/{pipeline}/run"
    logger.info("Sending request to %s for %r", url, question)
    resp = requests.post(url, data=json.dumps(payload))
    resp_json = resp.json()
    logger.info(pformat(resp_json))
    result = resp_json["result"]
    for word in re.split(r"(\W)", result):
        # simulate streaming response
        yield word
        time.sleep(0.01)


def decode_chunk(chunk):
    # Server-Sent Events (SSE) standard specifies that each chunk starts with `data: `,
    # distinguishing data from other possible fields like `event:` or `id:`
    decoded_line = chunk
    if decoded_line.startswith("data: "):
        jchunk = json.loads(decoded_line.removeprefix("data: "))
        logger.info("Received json chunk: %s", pformat(jchunk))
        return jchunk["choices"][0]["delta"]["content"]
    else:
        logger.info("Received non-data chunk: %r", decoded_line)
        return decoded_line


# To test, try 'Write a short poem about where Jean lives'
def create_streaming_response(question):
    payload = {"model": pipeline, "messages": [{"role": "user", "content": question}]}
    url = f"{HAYHOOKS_URL}/chat/completions"
    logger.info("Sending request to %s for %r", url, question)
    with requests.post(
        url,
        # headers={"Content-Type": "application/json", "Accept": "application/json"},
        stream=True,
        data=json.dumps(payload),
    ) as response:
        if response.ok:
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                yield decode_chunk(chunk)
        else:
            logger.info(f"Request failed with status code: {response.status_code}")
            response.raise_for_status()


if prompt:
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.write(f"({pipeline} model's response)")
        if stream_response:
            stream = create_streaming_response(prompt)
        else:
            stream = simulated_response_generator(prompt)
        full_response = st.write_stream(stream)
        logger.info("Full response: %s", full_response)
    with st.expander("Raw response", expanded=False):
        st.code(full_response, language="markdown")

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
