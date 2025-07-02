# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.opportunity_v1_api_base import BaseOpportunityV1Api
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
from pydantic import StrictInt
from typing import Optional
from openapi_server.models.error_response import ErrorResponse
from openapi_server.models.opportunity_get_response_v1 import OpportunityGetResponseV1
from openapi_server.models.opportunity_search_request_v1 import OpportunitySearchRequestV1
from openapi_server.models.opportunity_search_response_v1 import OpportunitySearchResponseV1
from openapi_server.security_api import get_token_ApiKeyAuth

router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/v1/opportunities/{opportunity_id}",
    responses={
        200: {"model": OpportunityGetResponseV1, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
    tags=["Opportunity v1"],
    summary="Opportunity Get",
    response_model_by_alias=True,
)
async def v1_opportunities_opportunity_id_get(
    opportunity_id: StrictInt = Path(..., description=""),
    token_ApiKeyAuth: TokenModel = Security(
        get_token_ApiKeyAuth
    ),
) -> OpportunityGetResponseV1:
    """ __ALPHA VERSION__  This endpoint in its current form is primarily for testing and feedback.  Features in this endpoint are still under heavy development, and subject to change. Not for production use.  See [Release Phases](https://github.com/github/roadmap?tab&#x3D;readme-ov-file#release-phases) for further details. """
    if not BaseOpportunityV1Api.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseOpportunityV1Api.subclasses[0]().v1_opportunities_opportunity_id_get(opportunity_id)


@router.post(
    "/v1/opportunities/search",
    responses={
        200: {"model": OpportunitySearchResponseV1, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    tags=["Opportunity v1"],
    summary="Opportunity Search",
    response_model_by_alias=True,
)
async def v1_opportunities_search_post(
    opportunity_search_request_v1: Optional[OpportunitySearchRequestV1] = Body(None, description=""),
    token_ApiKeyAuth: TokenModel = Security(
        get_token_ApiKeyAuth
    ),
) -> OpportunitySearchResponseV1:
    """ __ALPHA VERSION__  This endpoint in its current form is primarily for testing and feedback.  Features in this endpoint are still under heavy development, and subject to change. Not for production use.  See [Release Phases](https://github.com/github/roadmap?tab&#x3D;readme-ov-file#release-phases) for further details. """
    if not BaseOpportunityV1Api.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseOpportunityV1Api.subclasses[0]().v1_opportunities_search_post(opportunity_search_request_v1)
