# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import StrictInt
from typing import Optional
from openapi_server.models.error_response import ErrorResponse
from openapi_server.models.opportunity_get_response_v1 import OpportunityGetResponseV1
from openapi_server.models.opportunity_search_request_v1 import OpportunitySearchRequestV1
from openapi_server.models.opportunity_search_response_v1 import OpportunitySearchResponseV1
from openapi_server.security_api import get_token_ApiKeyAuth

class BaseOpportunityV1Api:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseOpportunityV1Api.subclasses = BaseOpportunityV1Api.subclasses + (cls,)
    async def v1_opportunities_opportunity_id_get(
        self,
        opportunity_id: StrictInt,
    ) -> OpportunityGetResponseV1:
        """ __ALPHA VERSION__  This endpoint in its current form is primarily for testing and feedback.  Features in this endpoint are still under heavy development, and subject to change. Not for production use.  See [Release Phases](https://github.com/github/roadmap?tab&#x3D;readme-ov-file#release-phases) for further details. """
        ...


    async def v1_opportunities_search_post(
        self,
        opportunity_search_request_v1: Optional[OpportunitySearchRequestV1],
    ) -> OpportunitySearchResponseV1:
        """ __ALPHA VERSION__  This endpoint in its current form is primarily for testing and feedback.  Features in this endpoint are still under heavy development, and subject to change. Not for production use.  See [Release Phases](https://github.com/github/roadmap?tab&#x3D;readme-ov-file#release-phases) for further details. """
        ...
