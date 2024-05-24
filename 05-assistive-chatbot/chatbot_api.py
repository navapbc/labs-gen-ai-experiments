from chainlit.server import app
from fastapi import Request
from fastapi.responses import (
    HTMLResponse,
)


# See https://docs.chainlit.io/deploy/api#how-it-works
@app.get("/hello")
def hello(request: Request):
    print(request.headers)
    return HTMLResponse("Hello World")


@app.get("/healthcheck")
def healthcheck():
    # TODO: Add a health check - https://pypi.org/project/fastapi-healthchecks/
    return HTMLResponse("Healthy")
