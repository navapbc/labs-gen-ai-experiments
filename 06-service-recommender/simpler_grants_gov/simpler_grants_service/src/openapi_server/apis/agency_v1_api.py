# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.agency_v1_api_base import BaseAgencyV1Api
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
from openapi_server.models.agency_list_request import AgencyListRequest
from openapi_server.models.agency_list_response import AgencyListResponse
from openapi_server.models.agency_search_request import AgencySearchRequest
from openapi_server.models.agency_search_response_v1 import AgencySearchResponseV1
from openapi_server.models.error_response import ErrorResponse
from openapi_server.security_api import get_token_ApiKeyAuth

router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/v1/agencies",
    responses={
        200: {"model": AgencyListResponse, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    tags=["Agency v1"],
    summary="Agencies Get",
    response_model_by_alias=True,
)
async def v1_agencies_post(
    agency_list_request: Optional[AgencyListRequest] = Body(None, description=""),
    token_ApiKeyAuth: TokenModel = Security(
        get_token_ApiKeyAuth
    ),
) -> AgencyListResponse:
    if not BaseAgencyV1Api.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAgencyV1Api.subclasses[0]().v1_agencies_post(agency_list_request)


@router.post(
    "/v1/agencies/search",
    responses={
        200: {"model": AgencySearchResponseV1, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    tags=["Agency v1"],
    summary="Agency Search",
    response_model_by_alias=True,
)
async def v1_agencies_search_post(
    agency_search_request: Optional[AgencySearchRequest] = Body(None, description=""),
    token_ApiKeyAuth: TokenModel = Security(
        get_token_ApiKeyAuth
    ),
) -> AgencySearchResponseV1:
    if not BaseAgencyV1Api.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAgencyV1Api.subclasses[0]().v1_agencies_search_post(agency_search_request)
