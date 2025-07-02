# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

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

class BaseUserV1InternalOnlyApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseUserV1InternalOnlyApi.subclasses = BaseUserV1InternalOnlyApi.subclasses + (cls,)
    async def v1_users_login_get(
        self,
    ) -> None:
        """ To use this endpoint, click [this link](/v1/users/login) which will redirect you to an OAuth provider where you can sign into an account.  Do not try to use the execute option below as OpenAPI will not redirect your browser for you.  The token you receive can then be set to the X-SGG-Token header for authenticating with endpoints. """
        ...


    async def v1_users_token_logout_post(
        self,
    ) -> UserTokenLogoutResponse:
        ...


    async def v1_users_token_refresh_post(
        self,
    ) -> UserTokenRefreshResponse:
        ...


    async def v1_users_user_id_get(
        self,
        user_id: StrictStr,
    ) -> UserGetResponse:
        ...


    async def v1_users_user_id_organizations_get(
        self,
        user_id: StrictStr,
    ) -> UserOrganizationsResponse:
        ...


    async def v1_users_user_id_saved_opportunities_list_post(
        self,
        user_id: StrictStr,
        user_saved_opportunities_request: Optional[UserSavedOpportunitiesRequest],
    ) -> UserSavedOpportunitiesResponse:
        ...


    async def v1_users_user_id_saved_opportunities_opportunity_id_delete(
        self,
        user_id: StrictStr,
        opportunity_id: StrictInt,
    ) -> UserDeleteSavedOpportunityResponse:
        ...


    async def v1_users_user_id_saved_opportunities_post(
        self,
        user_id: StrictStr,
        user_save_opportunity_request: Optional[UserSaveOpportunityRequest],
    ) -> UserSaveOpportunityResponse:
        ...


    async def v1_users_user_id_saved_searches_list_post(
        self,
        user_id: StrictStr,
        user_saved_searches_request: Optional[UserSavedSearchesRequest],
    ) -> UserSavedSearchesResponse:
        ...


    async def v1_users_user_id_saved_searches_post(
        self,
        user_id: StrictStr,
        user_save_search_request: Optional[UserSaveSearchRequest],
    ) -> UserSaveSearchResponse:
        ...


    async def v1_users_user_id_saved_searches_saved_search_id_delete(
        self,
        user_id: StrictStr,
        saved_search_id: StrictStr,
    ) -> UserDeleteSavedSearchResponse:
        ...


    async def v1_users_user_id_saved_searches_saved_search_id_put(
        self,
        user_id: StrictStr,
        saved_search_id: StrictStr,
        user_update_saved_search_request: Optional[UserUpdateSavedSearchRequest],
    ) -> UserUpdateSavedSearchResponse:
        ...
