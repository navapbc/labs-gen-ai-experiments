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

import dotenv
from fastapi import Body, FastAPI, Request, status
from pydantic import BaseModel

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
        settings = chatbot.create_init_settings()
        chatbot.validate_settings(settings)

        # Create the chat engine
        return chatbot.create_chat_engine(settings)


app_state = ApiState()


# This function cannot be async because it uses a single non-thread-safe app_state
@app.post("/query")
def query(message: str):
    response = app_state.chat_engine.gen_response(message)
    return response


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str
    build_date: str
    git_sha: str
    service_name: str
    hostname: str


@app.get(
    "/healthcheck",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
async def healthcheck(request: Request) -> HealthCheck:
    # Make sure to use async functions for faster responses
    logger.info(request.headers)

    git_sha = os.environ.get("GIT_SHA", "")
    build_date = os.environ.get("BUILD_DATE", "")

    service_name = os.environ.get("SERVICE_NAME", "")
    hostname = f"{platform.node()} {socket.gethostname()}"

    logger.info(f"Healthy {git_sha} built at {build_date}<br/>{service_name} {hostname}")
    return HealthCheck(
        build_date=build_date, git_sha=git_sha, status="OK", service_name=service_name, hostname=hostname
    )


ALLOWED_ENV_VARS = [
    "ROOT_LOG_LEVEL",
    "CHATBOT_LOG_LEVEL",
    "ENGINE_MODULES",
    "LLM_MODULES",
    "PRELOAD_CHAT_ENGINE",
    "CHAT_ENGINE",
    "LLM_MODEL_NAME",
    "LLM_TEMPERATURE",
    "RETRIEVE_K",
]


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
