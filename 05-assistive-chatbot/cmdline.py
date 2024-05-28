#!/usr/bin/env python3

"""
Commandline interface for running the same operations as the chatbot.
Useful for development, debugging, and testing.
"""

import logging

import chatbot

logger = logging.getLogger(f"chatbot.{__name__}")

# Load the initial settings
settings = chatbot.initial_settings
chatbot.validate_settings(settings)

# Create the chat engine
chat_engine = chatbot.create_chat_engine(settings)

# Query the chat engine
message = "Hello, what's your name?"
response = chat_engine.gen_response(message)

# Check the response type in case the chat_engine returns a non-string object
if not isinstance(response, str):
    logger.error("Unexpected type: %s", type(response))

print(response)
