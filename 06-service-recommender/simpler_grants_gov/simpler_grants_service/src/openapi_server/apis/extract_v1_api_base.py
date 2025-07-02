# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from typing import Optional
from openapi_server.models.error_response import ErrorResponse
from openapi_server.models.extract_metadata_list_response import ExtractMetadataListResponse
from openapi_server.models.extract_metadata_request import ExtractMetadataRequest
from openapi_server.security_api import get_token_ApiKeyAuth

class BaseExtractV1Api:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseExtractV1Api.subclasses = BaseExtractV1Api.subclasses + (cls,)
    async def v1_extracts_post(
        self,
        extract_metadata_request: Optional[ExtractMetadataRequest],
    ) -> ExtractMetadataListResponse:
        ...
