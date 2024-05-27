#!/usr/bin/env python3

"""
This is a sample API file that demonstrates how to create an API using FastAPI,
which is compatible with Chainlit. This file is a starting point for creating
an API that can be deployed with the Chainlit chatbot.
"""

import logging

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

_chat_engine = None


def chat_engine():
    # pylint: disable=global-statement
    global _chat_engine
    if not _chat_engine:
        # Load the initial settings
        settings = chatbot.initial_settings
        chatbot.validate_settings(settings)

        # Create the chat engine
        _chat_engine = chatbot.create_chat_engine(settings)

    return _chat_engine


# See https://docs.chainlit.io/deploy/api#how-it-works
@app.get("/query/{message}")
def query(message: str):
    response = chat_engine().gen_response(message)
    return HTMLResponse(response)


@app.get("/healthcheck")
def healthcheck(request: Request):
    logger.info(request.headers)
    # TODO: Add a health check - https://pypi.org/project/fastapi-healthchecks/
    return HTMLResponse("Healthy")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("__main__:app", host="0.0.0.0", port=8001, log_level="info")
