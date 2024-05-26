#!/usr/bin/env python3

import logging

import chatbot

logger = logging.getLogger(f"chatbot.{__name__}")


settings = chatbot.initial_settings
chatbot.validate_settings(settings)

chat_engine = chatbot.create_chat_engine(settings)

message = "Hello, what's your name?"
response = chat_engine.get_response(message)
if not isinstance(response, str):
    logger.error("Unexpected type: %s", type(response))

print(response)
