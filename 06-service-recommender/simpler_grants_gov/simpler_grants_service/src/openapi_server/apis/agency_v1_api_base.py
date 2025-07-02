# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from typing import Optional
from openapi_server.models.agency_list_request import AgencyListRequest
from openapi_server.models.agency_list_response import AgencyListResponse
from openapi_server.models.agency_search_request import AgencySearchRequest
from openapi_server.models.agency_search_response_v1 import AgencySearchResponseV1
from openapi_server.models.error_response import ErrorResponse
from openapi_server.security_api import get_token_ApiKeyAuth

class BaseAgencyV1Api:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseAgencyV1Api.subclasses = BaseAgencyV1Api.subclasses + (cls,)
    async def v1_agencies_post(
        self,
        agency_list_request: Optional[AgencyListRequest],
    ) -> AgencyListResponse:
        ...


    async def v1_agencies_search_post(
        self,
        agency_search_request: Optional[AgencySearchRequest],
    ) -> AgencySearchResponseV1:
        ...
