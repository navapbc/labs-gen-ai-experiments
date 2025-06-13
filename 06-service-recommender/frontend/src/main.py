# https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps#build-a-simple-chatbot-gui-with-streaming

import os
import random
import time
import json
from pprint import pprint
import requests
import streamlit as st

st.title("Simple chat")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

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

HAYHOOKS_URL = os.environ.get("HAYHOOKS_URL", "http://localhost:1416")


# Streamed response emulator
def simulated_response_generator(question):
    # Send POST request to the backend
    payload = {"question": question}
    pipeline = random.choice(["first", "second"])
    print(f"Sending request to {HAYHOOKS_URL}/{pipeline}/run for {question!r}")
    resp = requests.post(f"{HAYHOOKS_URL}/{pipeline}/run", data=json.dumps(payload))
    resp_json = resp.json()
    pprint(resp_json)
    result = resp_json["result"]
    for word in result.split():
        # simulate streaming response
        yield word + " "
        time.sleep(0.05)


def decode_chunk(chunk):
    # Server-Sent Events (SSE) standard specifies that each chunk starts with `data: `,
    # distinguishing data from other possible fields like `event:` or `id:`
    decoded_line = chunk
    if decoded_line.startswith("data: "):
        jchunk = json.loads(decoded_line.removeprefix("data: "))
        print("Received json chunk:")
        pprint(jchunk)
        return jchunk["choices"][0]["delta"]["content"]
    else:
        print("Received non-data chunk:", decoded_line)
        return decoded_line


# To test, try 'Write a short poem about where Jean lives'
def create_streaming_response(question):
    pipeline = random.choice(["first", "second"])
    payload = {"model": pipeline, "messages": [{"role": "user", "content": question}]}
    url = f"{HAYHOOKS_URL}/chat/completions"
    print(f"Sending request to {url} for {question!r}")
    yield f"{pipeline} model's response:\n"
    with requests.post(
        url,
        # headers={"Content-Type": "application/json", "Accept": "application/json"},
        stream=True,
        data=json.dumps(payload),
    ) as response:
        if response.ok:
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    # Process the chunk of data
                    # print(f"Received chunk: {chunk}")
                    yield decode_chunk(chunk)
        else:
            print(f"Request failed with status code: {response.status_code}")
            response.raise_for_status()


if prompt:
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        # stream = simulated_response_generator(prompt)
        stream = create_streaming_response(prompt)
        full_response = st.write_stream(stream)
        print("Full response:", full_response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
