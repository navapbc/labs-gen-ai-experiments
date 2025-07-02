# coding: utf-8

from fastapi.testclient import TestClient


from typing import Optional  # noqa: F401
from openapi_server.models.error_response import ErrorResponse  # noqa: F401
from openapi_server.models.extract_metadata_list_response import ExtractMetadataListResponse  # noqa: F401
from openapi_server.models.extract_metadata_request import ExtractMetadataRequest  # noqa: F401


def test_v1_extracts_post(client: TestClient):
    """Test case for v1_extracts_post

    Extract Metadata Get
    """
    extract_metadata_request = {"pagination":{"page_offset":1,"sort_order":[{"sort_direction":"ascending","order_by":"created_at"},{"sort_direction":"ascending","order_by":"created_at"},{"sort_direction":"ascending","order_by":"created_at"},{"sort_direction":"ascending","order_by":"created_at"},{"sort_direction":"ascending","order_by":"created_at"}],"page_size":25},"status_code":200,"data":"","filters":{"extract_type":"opportunities_json","created_at":{"end_date":"2000-01-23","start_date":"2000-01-23"}},"message":"Success"}

    headers = {
        "ApiKeyAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/extracts",
    #    headers=headers,
    #    json=extract_metadata_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

