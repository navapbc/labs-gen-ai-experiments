# coding: utf-8

from typing import List

from fastapi import Depends, Security  # noqa: F401
from fastapi.openapi.models import OAuthFlowImplicit, OAuthFlows  # noqa: F401
from fastapi.security import (  # noqa: F401
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
    OAuth2,
    OAuth2AuthorizationCodeBearer,
    OAuth2PasswordBearer,
    SecurityScopes,
)
from fastapi.security.api_key import APIKeyCookie, APIKeyHeader, APIKeyQuery  # noqa: F401

from openapi_server.models.extra_models import TokenModel


def get_token_apiKeyHeader(
    token_api_key_header: str = Security(
        APIKeyHeader(name="Api-Key", auto_error=False)
    ),
) -> TokenModel:
    """
    Check and retrieve authentication information from api_key.

    :param token_api_key_header API key provided by Authorization[Api-Key] header
    
    
    :type token_api_key_header: str
    :return: Information attached to provided api_key or None if api_key is invalid or does not allow access to called API
    :rtype: TokenModel | None
    """

    ...


def get_token_apiKeyQuery(
    
    token_api_key_query: str = Security(
        APIKeyQuery(name="api-key", auto_error=False)
    ),
) -> TokenModel:
    """
    Check and retrieve authentication information from api_key.

    
    
    :param token_api_key_query API key provided by [api-key] query
    :type token_api_key_query: str
    :return: Information attached to provided api_key or None if api_key is invalid or does not allow access to called API
    :rtype: TokenModel | None
    """

    ...

