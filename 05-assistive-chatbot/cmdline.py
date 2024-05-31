#!/usr/bin/env python3
"""
Commandline interface for running the same operations as the chatbot.
Useful for development, debugging, and testing.
"""

import dataclasses
import json
import logging

import chatbot
from chatbot import llms
from chatbot.engines import v2_household_engine

logger = logging.getLogger(f"chatbot.{__name__}")

# Load the initial settings
settings = chatbot.initial_settings
chatbot.validate_settings(settings)

# List LLMs, when CHATBOT_LOG_LEVEL=DEBUG
llms.available_llms()

# Create the chat engine
chat_engine = chatbot.create_chat_engine(settings)

# Query the chat engine
message = "Hello, what's your name?"
response = chat_engine.gen_response(message)

# Check the response type in case the chat_engine returns a non-string object
if isinstance(response, v2_household_engine.GenerationResults):
    response = json.dumps(dataclasses.asdict(response), indent=2)

print(response)
