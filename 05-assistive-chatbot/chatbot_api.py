#!/usr/bin/env python3

"""
This is a sample API file that demonstrates how to create an API using FastAPI,
which is compatible with Chainlit. This file is a starting point for creating
an API that can be deployed with the Chainlit chatbot.
"""

import logging
import os
import platform
import socket
from functools import cached_property
from io import StringIO
from typing import Dict

import dotenv
from fastapi import Body, FastAPI, Request
from fastapi.responses import HTMLResponse

import chatbot

if __name__ == "__main__":
    # If running directly, define the FastAPI app
    app = FastAPI()
else:
    # Otherwise use Chainlit's app
    # See https://docs.chainlit.io/deploy/api#how-it-works
    from chainlit.server import app

logger = logging.getLogger(f"chatbot.{__name__}")


class ApiState:
    @cached_property
    def chat_engine(self):
        # Load the initial settings
        settings = chatbot.initial_settings
        chatbot.validate_settings(settings)

        # Create the chat engine
        return chatbot.create_chat_engine(settings)


app_state = ApiState()


# This function cannot be async because it uses a single non-thread-safe app_state
@app.post("/query")
def query(message: str | Dict):
    response = app_state.chat_engine().gen_response(message)
    return response


# Make sure to use async functions for faster responses
@app.get("/healthcheck")
async def healthcheck(request: Request):
    logger.info(request.headers)
    # TODO: Add a health check - https://pypi.org/project/fastapi-healthchecks/

    git_sha = os.environ.get("GIT_SHA", "")
    build_date = os.environ.get("BUILD_DATE", "")
    hostname = f"{platform.node()} {socket.gethostname()}"

    logger.info("Returning: Healthy %s %s", build_date, git_sha)
    return HTMLResponse(f"Healthy {git_sha} built at {build_date}<br/>{hostname}")


ALLOWED_ENV_VARS = ["CHATBOT_LOG_LEVEL"]


@app.post("/initenvs")
def initenvs(env_file_contents: str = Body()):
    "Set environment variables for API keys and log level. See usage in push_image.yml"
    env_values = dotenv.dotenv_values(stream=StringIO(env_file_contents))
    vars_updated = []
    for name, value in env_values.items():
        if name.endswith("_API_KEY") or name.endswith("_API_TOKEN") or name in ALLOWED_ENV_VARS:
            logger.info("Setting environment variable %s", name)
            os.environ[name] = value or ""
            vars_updated.append(name)
        else:
            logger.warning("Setting environment variable %s is not allowed!", name)
    chatbot.reset()
    return str(vars_updated)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("__main__:app", host="0.0.0.0", port=8001, log_level="info")
