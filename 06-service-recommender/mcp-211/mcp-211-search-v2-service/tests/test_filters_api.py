# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field, StrictStr  # noqa: F401
from typing import Any, Dict, List, Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from openapi_server.models.data_owner_dto import DataOwnerDto  # noqa: F401


def test_get_filters_data_owners(client: TestClient):
    """Test case for get_filters_data_owners

    Filter: Data Owners
    """

    headers = {
        "apiKeyQuery": "special-key",
        "apiKeyHeader": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/filters/data-owners",
    #    headers=headers,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_filters_location_values_type_type_dataowners_dataowners(client: TestClient):
    """Test case for get_filters_location_values_type_type_dataowners_dataowners

    Filter: Location Geographies
    """
    params = [("type", 'type_example'),     ("data_owners", 'data_owners_example'),     ("type_filter", 'type_filter_example'),     ("type_filter_values", 'type_filter_values_example')]
    headers = {
        "apiKeyQuery": "special-key",
        "apiKeyHeader": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/filters/location-values",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_filters_service_area_values_type_type_dataowners_dataowners(client: TestClient):
    """Test case for get_filters_service_area_values_type_type_dataowners_dataowners

    Filter: Service Area Geographies
    """
    params = [("type", 'type_example'),     ("data_owners", 'data_owners_example'),     ("type_filter", 'type_filter_example'),     ("type_filter_values", 'type_filter_values_example')]
    headers = {
        "apiKeyQuery": "special-key",
        "apiKeyHeader": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/filters/service-area-values",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_filters_tags_dataowners_dataowners(client: TestClient):
    """Test case for get_filters_tags_dataowners_dataowners

    Filter: Tags
    """
    params = [("data_owners", 'data_owners_example')]
    headers = {
        "apiKeyQuery": "special-key",
        "apiKeyHeader": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/filters/tags",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_filters_target_terms_assigned_dataowners_dataowners(client: TestClient):
    """Test case for get_filters_target_terms_assigned_dataowners_dataowners

    Filter: Service Target Term Values Assigned
    """
    params = [("data_owners", 'data_owners_example')]
    headers = {
        "apiKeyQuery": "special-key",
        "apiKeyHeader": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/filters/target-terms-assigned",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_filters_taxonomy_level2_terms(client: TestClient):
    """Test case for get_filters_taxonomy_level2_terms

    Filter: Taxonomy Level 2 Terms with Level 1 Parent
    """
    params = [("data_owners", 'data_owners_example')]
    headers = {
        "apiKeyQuery": "special-key",
        "apiKeyHeader": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/filters/taxonomy-level2-terms",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_filters_taxonomy_terms_and_codes_assigned_level_level_levelterm_levelter(client: TestClient):
    """Test case for get_filters_taxonomy_terms_and_codes_assigned_level_level_levelterm_levelter

    Filter: Taxonomy Term and Code Values Assigned
    """
    params = [("level", 'level_example'),     ("level_term", 'level_term_example'),     ("data_owners", 'data_owners_example')]
    headers = {
        "apiKeyQuery": "special-key",
        "apiKeyHeader": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/filters/taxonomy-terms-and-codes-assigned",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_filters_taxonomy_terms_assigned_level_level_levelterm_levelterm_dataowne(client: TestClient):
    """Test case for get_filters_taxonomy_terms_assigned_level_level_levelterm_levelterm_dataowne

    Filter: Taxonomy Term Values Assigned
    """
    params = [("level", 'level_example'),     ("level_term", 'level_term_example'),     ("data_owners", 'data_owners_example')]
    headers = {
        "apiKeyQuery": "special-key",
        "apiKeyHeader": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/filters/taxonomy-terms-assigned",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_get_filters_taxonomy_terms_by_level_level_level(client: TestClient):
    """Test case for get_filters_taxonomy_terms_by_level_level_level

    Filter: Taxonomy Term Values By Level
    """
    params = [("level", 'level_example'),     ("data_owners", 'data_owners_example')]
    headers = {
        "apiKeyQuery": "special-key",
        "apiKeyHeader": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/filters/taxonomy-terms-by-level",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

