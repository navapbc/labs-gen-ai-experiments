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
def response_generator(question):
    # Send POST request to the backend
    payload = {"question": question}
    pipeline = random.choice(["first", "second"])
    print(f"Sending request to {HAYHOOKS_URL}/{pipeline}/run for {question!r}")
    resp = requests.post(f"{HAYHOOKS_URL}/{pipeline}/run", data=json.dumps(payload))
    resp_json = resp.json()
    pprint(resp_json)
    result = resp_json["result"]

    # TODO: implement streaming response
    for word in result.split():
        # simulate streaming response
        yield word + " "
        time.sleep(0.05)


if prompt:
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(prompt))
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
