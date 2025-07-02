# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.extract_v1_api_base import BaseExtractV1Api
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
from typing import Optional
from openapi_server.models.error_response import ErrorResponse
from openapi_server.models.extract_metadata_list_response import ExtractMetadataListResponse
from openapi_server.models.extract_metadata_request import ExtractMetadataRequest
from openapi_server.security_api import get_token_ApiKeyAuth

router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/v1/extracts",
    responses={
        200: {"model": ExtractMetadataListResponse, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    tags=["Extract v1"],
    summary="Extract Metadata Get",
    response_model_by_alias=True,
)
async def v1_extracts_post(
    extract_metadata_request: Optional[ExtractMetadataRequest] = Body(None, description=""),
    token_ApiKeyAuth: TokenModel = Security(
        get_token_ApiKeyAuth
    ),
) -> ExtractMetadataListResponse:
    if not BaseExtractV1Api.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExtractV1Api.subclasses[0]().v1_extracts_post(extract_metadata_request)
