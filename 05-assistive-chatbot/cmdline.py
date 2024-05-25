#!/usr/bin/env python3
import core

settings = core.initial_settings
core.validate_settings(settings)

chat_engine = core.create_chat_engine(settings)

message = "Hello, world!"
response = chat_engine.get_response(message)
print(response)
