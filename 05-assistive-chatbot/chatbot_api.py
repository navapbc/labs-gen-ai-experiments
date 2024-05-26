import logging

from chainlit.server import app
from fastapi import Request
from fastapi.responses import HTMLResponse

logger = logging.getLogger(f"chatbot.{__name__}")


# See https://docs.chainlit.io/deploy/api#how-it-works
@app.get("/hello")
def hello(request: Request):
    logger.info(request.headers)
    return HTMLResponse("Hello World")


@app.get("/healthcheck")
def healthcheck():
    # TODO: Add a health check - https://pypi.org/project/fastapi-healthchecks/
    return HTMLResponse("Healthy")
