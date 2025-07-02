# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import StrictInt, StrictStr  # noqa: F401
from typing import Any, Optional  # noqa: F401
from openapi_server.models.error_response import ErrorResponse  # noqa: F401
from openapi_server.models.user_delete_saved_opportunity_response import UserDeleteSavedOpportunityResponse  # noqa: F401
from openapi_server.models.user_delete_saved_search_response import UserDeleteSavedSearchResponse  # noqa: F401
from openapi_server.models.user_get_response import UserGetResponse  # noqa: F401
from openapi_server.models.user_organizations_response import UserOrganizationsResponse  # noqa: F401
from openapi_server.models.user_save_opportunity_request import UserSaveOpportunityRequest  # noqa: F401
from openapi_server.models.user_save_opportunity_response import UserSaveOpportunityResponse  # noqa: F401
from openapi_server.models.user_save_search_request import UserSaveSearchRequest  # noqa: F401
from openapi_server.models.user_save_search_response import UserSaveSearchResponse  # noqa: F401
from openapi_server.models.user_saved_opportunities_request import UserSavedOpportunitiesRequest  # noqa: F401
from openapi_server.models.user_saved_opportunities_response import UserSavedOpportunitiesResponse  # noqa: F401
from openapi_server.models.user_saved_searches_request import UserSavedSearchesRequest  # noqa: F401
from openapi_server.models.user_saved_searches_response import UserSavedSearchesResponse  # noqa: F401
from openapi_server.models.user_token_logout_response import UserTokenLogoutResponse  # noqa: F401
from openapi_server.models.user_token_refresh_response import UserTokenRefreshResponse  # noqa: F401
from openapi_server.models.user_update_saved_search_request import UserUpdateSavedSearchRequest  # noqa: F401
from openapi_server.models.user_update_saved_search_response import UserUpdateSavedSearchResponse  # noqa: F401


def test_v1_users_login_get(client: TestClient):
    """Test case for v1_users_login_get

    User Login
    """

    headers = {
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/users/login",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_v1_users_token_logout_post(client: TestClient):
    """Test case for v1_users_token_logout_post

    User Token Logout
    """

    headers = {
        "ApiJwtAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/users/token/logout",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_v1_users_token_refresh_post(client: TestClient):
    """Test case for v1_users_token_refresh_post

    User Token Refresh
    """

    headers = {
        "ApiJwtAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/users/token/refresh",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_v1_users_user_id_get(client: TestClient):
    """Test case for v1_users_user_id_get

    User Get
    """

    headers = {
        "ApiJwtAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/users/{user_id}".format(user_id='user_id_example'),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_v1_users_user_id_organizations_get(client: TestClient):
    """Test case for v1_users_user_id_organizations_get

    User Get Organizations
    """

    headers = {
        "ApiJwtAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/v1/users/{user_id}/organizations".format(user_id='user_id_example'),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_v1_users_user_id_saved_opportunities_list_post(client: TestClient):
    """Test case for v1_users_user_id_saved_opportunities_list_post

    User Get Saved Opportunities
    """
    user_saved_opportunities_request = {"pagination":{"page_offset":1,"sort_order":[{"sort_direction":"ascending","order_by":"created_at"},{"sort_direction":"ascending","order_by":"created_at"},{"sort_direction":"ascending","order_by":"created_at"},{"sort_direction":"ascending","order_by":"created_at"},{"sort_direction":"ascending","order_by":"created_at"}],"page_size":25}}

    headers = {
        "ApiJwtAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/users/{user_id}/saved-opportunities/list".format(user_id='user_id_example'),
    #    headers=headers,
    #    json=user_saved_opportunities_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_v1_users_user_id_saved_opportunities_opportunity_id_delete(client: TestClient):
    """Test case for v1_users_user_id_saved_opportunities_opportunity_id_delete

    User Delete Saved Opportunity
    """

    headers = {
        "ApiJwtAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "DELETE",
    #    "/v1/users/{user_id}/saved-opportunities/{opportunity_id}".format(user_id='user_id_example', opportunity_id=56),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_v1_users_user_id_saved_opportunities_post(client: TestClient):
    """Test case for v1_users_user_id_saved_opportunities_post

    User Save Opportunity
    """
    user_save_opportunity_request = {"opportunity_id":0}

    headers = {
        "ApiJwtAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/users/{user_id}/saved-opportunities".format(user_id='user_id_example'),
    #    headers=headers,
    #    json=user_save_opportunity_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_v1_users_user_id_saved_searches_list_post(client: TestClient):
    """Test case for v1_users_user_id_saved_searches_list_post

    User Get Saved Searches
    """
    user_saved_searches_request = {"pagination":{"page_offset":1,"sort_order":[{"sort_direction":"ascending","order_by":"created_at"},{"sort_direction":"ascending","order_by":"created_at"},{"sort_direction":"ascending","order_by":"created_at"},{"sort_direction":"ascending","order_by":"created_at"},{"sort_direction":"ascending","order_by":"created_at"}],"page_size":25}}

    headers = {
        "ApiJwtAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/users/{user_id}/saved-searches/list".format(user_id='user_id_example'),
    #    headers=headers,
    #    json=user_saved_searches_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_v1_users_user_id_saved_searches_post(client: TestClient):
    """Test case for v1_users_user_id_saved_searches_post

    User Save Search
    """
    user_save_search_request = {"name":"Example search","search_query":{"query_operator":"OR","pagination":{"page_offset":1,"sort_order":[{"sort_direction":"ascending","order_by":"relevancy"},{"sort_direction":"ascending","order_by":"relevancy"},{"sort_direction":"ascending","order_by":"relevancy"},{"sort_direction":"ascending","order_by":"relevancy"},{"sort_direction":"ascending","order_by":"relevancy"}],"page_size":25},"query":"research","format":"json","experimental":{"scoring_rule":"default"},"filters":{"close_date":{"end_date":"2000-01-23","start_date_relative":205491,"end_date_relative":-839834,"start_date":"2000-01-23"},"is_cost_sharing":{"one_of":[1,1]},"agency":{"one_of":["USAID","USAID"]},"award_ceiling":{"min":0,"max":10000000},"expected_number_of_awards":{"min":0,"max":25},"funding_instrument":{"one_of":["cooperative_agreement","cooperative_agreement"]},"assistance_listing_number":{"one_of":["45.149","45.149"]},"award_floor":{"min":0,"max":10000},"opportunity_status":{"one_of":["forecasted","forecasted"]},"top_level_agency":{"one_of":["USAID","USAID"]},"post_date":{"end_date":"2000-01-23","start_date_relative":205491,"end_date_relative":-839834,"start_date":"2000-01-23"},"funding_category":{"one_of":["recovery_act","recovery_act"]},"estimated_total_program_funding":{"min":0,"max":10000000},"applicant_type":{"one_of":["state_governments","state_governments"]}}}}

    headers = {
        "ApiJwtAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/v1/users/{user_id}/saved-searches".format(user_id='user_id_example'),
    #    headers=headers,
    #    json=user_save_search_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_v1_users_user_id_saved_searches_saved_search_id_delete(client: TestClient):
    """Test case for v1_users_user_id_saved_searches_saved_search_id_delete

    User Delete Saved Search
    """

    headers = {
        "ApiJwtAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "DELETE",
    #    "/v1/users/{user_id}/saved-searches/{saved_search_id}".format(user_id='user_id_example', saved_search_id='saved_search_id_example'),
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_v1_users_user_id_saved_searches_saved_search_id_put(client: TestClient):
    """Test case for v1_users_user_id_saved_searches_saved_search_id_put

    User Update Saved Search
    """
    user_update_saved_search_request = {"name":"Example search"}

    headers = {
        "ApiJwtAuth": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "PUT",
    #    "/v1/users/{user_id}/saved-searches/{saved_search_id}".format(user_id='user_id_example', saved_search_id='saved_search_id_example'),
    #    headers=headers,
    #    json=user_update_saved_search_request,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

