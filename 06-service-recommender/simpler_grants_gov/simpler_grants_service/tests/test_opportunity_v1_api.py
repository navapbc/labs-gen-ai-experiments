# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import StrictInt  # noqa: F401
from typing import Optional  # noqa: F401
from openapi_server.models.error_response import ErrorResponse  # noqa: F401
from openapi_server.models.opportunity_get_response_v1 import OpportunityGetResponseV1  # noqa: F401
from openapi_server.models.opportunity_search_request_v1 import OpportunitySearchRequestV1  # noqa: F401
from openapi_server.models.opportunity_search_response_v1 import OpportunitySearchResponseV1  # noqa: F401


def test_v1_opportunities_opportunity_id_get(client: TestClient):
    """Test case for v1_opportunities_opportunity_id_get

    Opportunity Get
    """

    headers = {
        "ApiKeyAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/opportunities/{opportunity_id}".format(opportunity_id=56),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_v1_opportunities_search_post(client: TestClient):
    """Test case for v1_opportunities_search_post

    Opportunity Search
    """
    opportunity_search_request_v1 = {"query_operator":"OR","pagination":{"page_offset":1,"sort_order":[{"sort_direction":"ascending","order_by":"relevancy"},{"sort_direction":"ascending","order_by":"relevancy"},{"sort_direction":"ascending","order_by":"relevancy"},{"sort_direction":"ascending","order_by":"relevancy"},{"sort_direction":"ascending","order_by":"relevancy"}],"page_size":25},"query":"research","format":"json","experimental":{"scoring_rule":"default"},"filters":{"close_date":{"end_date":"2000-01-23","start_date_relative":205491,"end_date_relative":-839834,"start_date":"2000-01-23"},"is_cost_sharing":{"one_of":[1,1]},"agency":{"one_of":["USAID","USAID"]},"award_ceiling":{"min":0,"max":10000000},"expected_number_of_awards":{"min":0,"max":25},"funding_instrument":{"one_of":["cooperative_agreement","cooperative_agreement"]},"assistance_listing_number":{"one_of":["45.149","45.149"]},"award_floor":{"min":0,"max":10000},"opportunity_status":{"one_of":["forecasted","forecasted"]},"top_level_agency":{"one_of":["USAID","USAID"]},"post_date":{"end_date":"2000-01-23","start_date_relative":205491,"end_date_relative":-839834,"start_date":"2000-01-23"},"funding_category":{"one_of":["recovery_act","recovery_act"]},"estimated_total_program_funding":{"min":0,"max":10000000},"applicant_type":{"one_of":["state_governments","state_governments"]}}}

    headers = {
        "ApiKeyAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/opportunities/search",
    #    headers=headers,
    #    json=opportunity_search_request_v1,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

