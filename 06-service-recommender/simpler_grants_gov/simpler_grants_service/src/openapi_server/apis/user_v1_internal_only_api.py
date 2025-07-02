# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.user_v1_internal_only_api_base import BaseUserV1InternalOnlyApi
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
from pydantic import StrictInt, StrictStr
from typing import Any, Optional
from openapi_server.models.error_response import ErrorResponse
from openapi_server.models.user_delete_saved_opportunity_response import UserDeleteSavedOpportunityResponse
from openapi_server.models.user_delete_saved_search_response import UserDeleteSavedSearchResponse
from openapi_server.models.user_get_response import UserGetResponse
from openapi_server.models.user_organizations_response import UserOrganizationsResponse
from openapi_server.models.user_save_opportunity_request import UserSaveOpportunityRequest
from openapi_server.models.user_save_opportunity_response import UserSaveOpportunityResponse
from openapi_server.models.user_save_search_request import UserSaveSearchRequest
from openapi_server.models.user_save_search_response import UserSaveSearchResponse
from openapi_server.models.user_saved_opportunities_request import UserSavedOpportunitiesRequest
from openapi_server.models.user_saved_opportunities_response import UserSavedOpportunitiesResponse
from openapi_server.models.user_saved_searches_request import UserSavedSearchesRequest
from openapi_server.models.user_saved_searches_response import UserSavedSearchesResponse
from openapi_server.models.user_token_logout_response import UserTokenLogoutResponse
from openapi_server.models.user_token_refresh_response import UserTokenRefreshResponse
from openapi_server.models.user_update_saved_search_request import UserUpdateSavedSearchRequest
from openapi_server.models.user_update_saved_search_response import UserUpdateSavedSearchResponse
from openapi_server.security_api import get_token_ApiJwtAuth

router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/v1/users/login",
    responses={
        302: {"model": object, "description": "Found"},
    },
    tags=["User v1 - Internal Only"],
    summary="User Login",
    response_model_by_alias=True,
)
async def v1_users_login_get(
) -> None:
    """ To use this endpoint, click [this link](/v1/users/login) which will redirect you to an OAuth provider where you can sign into an account.  Do not try to use the execute option below as OpenAPI will not redirect your browser for you.  The token you receive can then be set to the X-SGG-Token header for authenticating with endpoints. """
    if not BaseUserV1InternalOnlyApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUserV1InternalOnlyApi.subclasses[0]().v1_users_login_get()


@router.post(
    "/v1/users/token/logout",
    responses={
        200: {"model": UserTokenLogoutResponse, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
    },
    tags=["User v1 - Internal Only"],
    summary="User Token Logout",
    response_model_by_alias=True,
)
async def v1_users_token_logout_post(
    token_ApiJwtAuth: TokenModel = Security(
        get_token_ApiJwtAuth
    ),
) -> UserTokenLogoutResponse:
    if not BaseUserV1InternalOnlyApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUserV1InternalOnlyApi.subclasses[0]().v1_users_token_logout_post()


@router.post(
    "/v1/users/token/refresh",
    responses={
        200: {"model": UserTokenRefreshResponse, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
    },
    tags=["User v1 - Internal Only"],
    summary="User Token Refresh",
    response_model_by_alias=True,
)
async def v1_users_token_refresh_post(
    token_ApiJwtAuth: TokenModel = Security(
        get_token_ApiJwtAuth
    ),
) -> UserTokenRefreshResponse:
    if not BaseUserV1InternalOnlyApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUserV1InternalOnlyApi.subclasses[0]().v1_users_token_refresh_post()


@router.get(
    "/v1/users/{user_id}",
    responses={
        200: {"model": UserGetResponse, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
    tags=["User v1 - Internal Only"],
    summary="User Get",
    response_model_by_alias=True,
)
async def v1_users_user_id_get(
    user_id: StrictStr = Path(..., description=""),
    token_ApiJwtAuth: TokenModel = Security(
        get_token_ApiJwtAuth
    ),
) -> UserGetResponse:
    if not BaseUserV1InternalOnlyApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUserV1InternalOnlyApi.subclasses[0]().v1_users_user_id_get(user_id)


@router.get(
    "/v1/users/{user_id}/organizations",
    responses={
        200: {"model": UserOrganizationsResponse, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
    tags=["User v1 - Internal Only"],
    summary="User Get Organizations",
    response_model_by_alias=True,
)
async def v1_users_user_id_organizations_get(
    user_id: StrictStr = Path(..., description=""),
    token_ApiJwtAuth: TokenModel = Security(
        get_token_ApiJwtAuth
    ),
) -> UserOrganizationsResponse:
    if not BaseUserV1InternalOnlyApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUserV1InternalOnlyApi.subclasses[0]().v1_users_user_id_organizations_get(user_id)


@router.post(
    "/v1/users/{user_id}/saved-opportunities/list",
    responses={
        200: {"model": UserSavedOpportunitiesResponse, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    tags=["User v1 - Internal Only"],
    summary="User Get Saved Opportunities",
    response_model_by_alias=True,
)
async def v1_users_user_id_saved_opportunities_list_post(
    user_id: StrictStr = Path(..., description=""),
    user_saved_opportunities_request: Optional[UserSavedOpportunitiesRequest] = Body(None, description=""),
    token_ApiJwtAuth: TokenModel = Security(
        get_token_ApiJwtAuth
    ),
) -> UserSavedOpportunitiesResponse:
    if not BaseUserV1InternalOnlyApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUserV1InternalOnlyApi.subclasses[0]().v1_users_user_id_saved_opportunities_list_post(user_id, user_saved_opportunities_request)


@router.delete(
    "/v1/users/{user_id}/saved-opportunities/{opportunity_id}",
    responses={
        200: {"model": UserDeleteSavedOpportunityResponse, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
    tags=["User v1 - Internal Only"],
    summary="User Delete Saved Opportunity",
    response_model_by_alias=True,
)
async def v1_users_user_id_saved_opportunities_opportunity_id_delete(
    user_id: StrictStr = Path(..., description=""),
    opportunity_id: StrictInt = Path(..., description=""),
    token_ApiJwtAuth: TokenModel = Security(
        get_token_ApiJwtAuth
    ),
) -> UserDeleteSavedOpportunityResponse:
    if not BaseUserV1InternalOnlyApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUserV1InternalOnlyApi.subclasses[0]().v1_users_user_id_saved_opportunities_opportunity_id_delete(user_id, opportunity_id)


@router.post(
    "/v1/users/{user_id}/saved-opportunities",
    responses={
        200: {"model": UserSaveOpportunityResponse, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    tags=["User v1 - Internal Only"],
    summary="User Save Opportunity",
    response_model_by_alias=True,
)
async def v1_users_user_id_saved_opportunities_post(
    user_id: StrictStr = Path(..., description=""),
    user_save_opportunity_request: Optional[UserSaveOpportunityRequest] = Body(None, description=""),
    token_ApiJwtAuth: TokenModel = Security(
        get_token_ApiJwtAuth
    ),
) -> UserSaveOpportunityResponse:
    if not BaseUserV1InternalOnlyApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUserV1InternalOnlyApi.subclasses[0]().v1_users_user_id_saved_opportunities_post(user_id, user_save_opportunity_request)


@router.post(
    "/v1/users/{user_id}/saved-searches/list",
    responses={
        200: {"model": UserSavedSearchesResponse, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    tags=["User v1 - Internal Only"],
    summary="User Get Saved Searches",
    response_model_by_alias=True,
)
async def v1_users_user_id_saved_searches_list_post(
    user_id: StrictStr = Path(..., description=""),
    user_saved_searches_request: Optional[UserSavedSearchesRequest] = Body(None, description=""),
    token_ApiJwtAuth: TokenModel = Security(
        get_token_ApiJwtAuth
    ),
) -> UserSavedSearchesResponse:
    if not BaseUserV1InternalOnlyApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUserV1InternalOnlyApi.subclasses[0]().v1_users_user_id_saved_searches_list_post(user_id, user_saved_searches_request)


@router.post(
    "/v1/users/{user_id}/saved-searches",
    responses={
        200: {"model": UserSaveSearchResponse, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    tags=["User v1 - Internal Only"],
    summary="User Save Search",
    response_model_by_alias=True,
)
async def v1_users_user_id_saved_searches_post(
    user_id: StrictStr = Path(..., description=""),
    user_save_search_request: Optional[UserSaveSearchRequest] = Body(None, description=""),
    token_ApiJwtAuth: TokenModel = Security(
        get_token_ApiJwtAuth
    ),
) -> UserSaveSearchResponse:
    if not BaseUserV1InternalOnlyApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUserV1InternalOnlyApi.subclasses[0]().v1_users_user_id_saved_searches_post(user_id, user_save_search_request)


@router.delete(
    "/v1/users/{user_id}/saved-searches/{saved_search_id}",
    responses={
        200: {"model": UserDeleteSavedSearchResponse, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
    tags=["User v1 - Internal Only"],
    summary="User Delete Saved Search",
    response_model_by_alias=True,
)
async def v1_users_user_id_saved_searches_saved_search_id_delete(
    user_id: StrictStr = Path(..., description=""),
    saved_search_id: StrictStr = Path(..., description=""),
    token_ApiJwtAuth: TokenModel = Security(
        get_token_ApiJwtAuth
    ),
) -> UserDeleteSavedSearchResponse:
    if not BaseUserV1InternalOnlyApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUserV1InternalOnlyApi.subclasses[0]().v1_users_user_id_saved_searches_saved_search_id_delete(user_id, saved_search_id)


@router.put(
    "/v1/users/{user_id}/saved-searches/{saved_search_id}",
    responses={
        200: {"model": UserUpdateSavedSearchResponse, "description": "Successful response"},
        401: {"model": ErrorResponse, "description": "Authentication error"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
    tags=["User v1 - Internal Only"],
    summary="User Update Saved Search",
    response_model_by_alias=True,
)
async def v1_users_user_id_saved_searches_saved_search_id_put(
    user_id: StrictStr = Path(..., description=""),
    saved_search_id: StrictStr = Path(..., description=""),
    user_update_saved_search_request: Optional[UserUpdateSavedSearchRequest] = Body(None, description=""),
    token_ApiJwtAuth: TokenModel = Security(
        get_token_ApiJwtAuth
    ),
) -> UserUpdateSavedSearchResponse:
    if not BaseUserV1InternalOnlyApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseUserV1InternalOnlyApi.subclasses[0]().v1_users_user_id_saved_searches_saved_search_id_put(user_id, saved_search_id, user_update_saved_search_request)
