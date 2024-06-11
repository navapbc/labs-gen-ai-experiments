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


from fastapi import FastAPI, Request, status
from pydantic import BaseModel


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

class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""
    
    status: str
    build_date: str
    git_sha: str


@app.get(
    "/healthcheck",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def healthcheck(request: Request) -> HealthCheck:
    logger.info(request.headers)

    git_sha = os.environ.get("GIT_SHA", "")
    build_date = os.environ.get("BUILD_DATE", "")
    
    logger.info("Returning: Healthy %s %s", build_date, git_sha)
    return HealthCheck(build_date=build_date, git_sha=git_sha, status="OK")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("__main__:app", host="0.0.0.0", port=8001, log_level="info")
