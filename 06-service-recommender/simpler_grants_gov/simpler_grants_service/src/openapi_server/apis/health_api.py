# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.health_api_base import BaseHealthApi
import openapi_server.impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from openapi_server.models.extra_models import TokenModel  # noqa: F401
from openapi_server.models.error_response import ErrorResponse
from openapi_server.models.healthcheck_response import HealthcheckResponse


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/health",
    responses={
        200: {"model": HealthcheckResponse, "description": "Successful response"},
        503: {"model": ErrorResponse, "description": "Service Unavailable"},
    },
    tags=["Health"],
    summary="Health",
    response_model_by_alias=True,
)
async def health_get(
) -> HealthcheckResponse:
    if not BaseHealthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseHealthApi.subclasses[0]().health_get()
