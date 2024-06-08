#!/usr/bin/env python3

"""
This is a sample API file that demonstrates how to create an API using FastAPI,
which is compatible with Chainlit. This file is a starting point for creating
an API that can be deployed with the Chainlit chatbot.
"""

import logging
import os
from functools import cached_property
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

import chatbot

if __name__ == "__main__":
    # If running directly, define the FastAPI app
    app = FastAPI()
else:
    # Otherwise use Chainlit's app
    from chainlit.server import app

logger = logging.getLogger(f"chatbot.{__name__}")


# TODO Ensure this is thread safe when run by via chalint. Check if the chainlit command might handle threading/multiple requests for us.
class ApiState:
    @cached_property
    def chat_engine(self):
        # Load the initial settings
        settings = chatbot.initial_settings
        chatbot.validate_settings(settings)

        # Create the chat engine
        return chatbot.create_chat_engine(settings)


app_state = ApiState()


# See https://docs.chainlit.io/deploy/api#how-it-works
@app.post("/query")
def query(message: str | Dict):
    response = app_state.chat_engine().gen_response(message)
    return response


@app.get("/healthcheck")
def healthcheck(request: Request):
    logger.info(request.headers)
    # TODO: Add a health check - https://pypi.org/project/fastapi-healthchecks/

    git_sha = os.environ.get("GIT_SHA", "")
    build_date = os.environ.get("BUILD_DATE", "")

    logger.info("Returning: Healthy %s %s", build_date, git_sha)
    return HTMLResponse(f"Healthy {git_sha} built at {build_date}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("__main__:app", host="0.0.0.0", port=8001, log_level="info")
