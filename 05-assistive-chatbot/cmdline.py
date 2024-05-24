#!/usr/bin/env python3
import core

settings = core.initial_settings
core.validate_settings(settings)

client = core.create_llm_client(settings)

message = "Hello, world!"
response = client.submit(message)
print(response)
