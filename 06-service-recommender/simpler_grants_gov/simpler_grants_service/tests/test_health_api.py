# coding: utf-8

from fastapi.testclient import TestClient


from openapi_server.models.error_response import ErrorResponse  # noqa: F401
from openapi_server.models.healthcheck_response import HealthcheckResponse  # noqa: F401


def test_health_get(client: TestClient):
    """Test case for health_get

    Health
    """

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/health",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

