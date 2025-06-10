# https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps#build-a-simple-chatbot-gui-with-streaming

import streamlit as st
import random
import time
import json
import requests

st.title("Simple chat")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

# Streamed response emulator
def response_generator(prompt):
    if prompt:
        # Send POST request to the backend (emulated here)
        payload = {"question": prompt}
        # TODO: Replace with actual backend URL
        url = "http://backend:1416/first/run"
        resp = requests.post(url, data=json.dumps(payload))
        resp_json = resp.json()
        response = resp_json["result"]
    else:
        response = random.choice(
            [
                "Hello there! How can I assist you today?",
                "Hi, human! Is there anything I can help you with?",
                "Do you need help?",
            ]
        )
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

# Display assistant response in chat message container
with st.chat_message("assistant"):
    response = st.write_stream(response_generator(prompt))
# Add assistant response to chat history
st.session_state.messages.append({"role": "assistant", "content": response})

