# coding: utf-8

from fastapi.testclient import TestClient


from typing import Optional  # noqa: F401
from openapi_server.models.agency_list_request import AgencyListRequest  # noqa: F401
from openapi_server.models.agency_list_response import AgencyListResponse  # noqa: F401
from openapi_server.models.agency_search_request import AgencySearchRequest  # noqa: F401
from openapi_server.models.agency_search_response_v1 import AgencySearchResponseV1  # noqa: F401
from openapi_server.models.error_response import ErrorResponse  # noqa: F401


def test_v1_agencies_post(client: TestClient):
    """Test case for v1_agencies_post

    Agencies Get
    """
    agency_list_request = {"pagination":{"page_offset":1,"sort_order":[{"sort_direction":"ascending","order_by":"agency_code"},{"sort_direction":"ascending","order_by":"agency_code"},{"sort_direction":"ascending","order_by":"agency_code"},{"sort_direction":"ascending","order_by":"agency_code"},{"sort_direction":"ascending","order_by":"agency_code"}],"page_size":25},"filters":{"agency_id":"123e4567-e89b-12d3-a456-426614174000","active":1}}

    headers = {
        "ApiKeyAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/agencies",
    #    headers=headers,
    #    json=agency_list_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_v1_agencies_search_post(client: TestClient):
    """Test case for v1_agencies_search_post

    Agency Search
    """
    agency_search_request = {"query_operator":"OR","pagination":{"page_offset":1,"sort_order":[{"sort_direction":"ascending","order_by":"agency_code"},{"sort_direction":"ascending","order_by":"agency_code"},{"sort_direction":"ascending","order_by":"agency_code"},{"sort_direction":"ascending","order_by":"agency_code"},{"sort_direction":"ascending","order_by":"agency_code"}],"page_size":25},"query":"research","filters":{"opportunity_statuses":{"one_of":["archived","archived"]},"has_active_opportunity":{"one_of":[1,1]},"is_test_agency":{"one_of":[1,1]}}}

    headers = {
        "ApiKeyAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/agencies/search",
    #    headers=headers,
    #    json=agency_search_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

