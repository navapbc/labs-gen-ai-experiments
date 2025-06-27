# coding: utf-8

from fastapi.testclient import TestClient


from pydantic import Field, StrictBool, StrictInt, StrictStr  # noqa: F401
from typing import Any, Optional  # noqa: F401
from typing_extensions import Annotated  # noqa: F401
from openapi_server.models.location_mode_dto import LocationModeDto  # noqa: F401
from openapi_server.models.location_type_dto import LocationTypeDto  # noqa: F401
from openapi_server.models.search_input_dto import SearchInputDto  # noqa: F401
from openapi_server.models.search_mode_dto import SearchModeDto  # noqa: F401
from openapi_server.models.search_output_dto import SearchOutputDto  # noqa: F401


def test_get_keyword_keywords_keywords_location_location(client: TestClient):
    """Test case for get_keyword_keywords_keywords_location_location

    Search: Keywords
    """
    params = [("keywords", 'keywords_example'),     ("location", 'location_example')]
    headers = {
        "distance": 56,
        "data_owners": 'data_owners_example',
        "tags_service": 'tags_service_example',
        "search_within_location_type": openapi_server.LocationTypeDto(),
        "skip": 0,
        "size": 10,
        "search_mode": openapi_server.SearchModeDto(),
        "location_mode": openapi_server.LocationModeDto(),
        "keyword_is_taxonomy_code": False,
        "keyword_is_taxonomy_term": False,
        "results_advanced": False,
        "order_by_distance": True,
        "taxonomy_terms": 'taxonomy_terms_example',
        "taxonomy_codes": 'taxonomy_codes_example',
        "target_terms": 'target_terms_example',
        "service_area_countries": 'service_area_countries_example',
        "service_area_states": 'service_area_states_example',
        "service_area_counties": 'service_area_counties_example',
        "service_area_cities": 'service_area_cities_example',
        "service_area_postal_codes": 'service_area_postal_codes_example',
        "address_countries": 'address_countries_example',
        "address_states": 'address_states_example',
        "address_counties": 'address_counties_example',
        "address_cities": 'address_cities_example',
        "address_postal_codes": 'address_postal_codes_example',
        "ids": 'ids_example',
        "apiKeyQuery": "special-key",
        "apiKeyHeader": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "GET",
    #    "/keyword",
    #    headers=headers,
    #    params=params,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200


def test_post_keyword(client: TestClient):
    """Test case for post_keyword

    Search: Keywords
    """
    search_input_dto = {"select_fields":["nameService","nameOrganization","descriptionService","tagsService"],"distance":6,"keyword_is_taxonomy_code":0,"search_mode":"All","skip":1,"filters":[{"field":"\r\n            dataOwner\r\n            ","operators":{"assert":"assert","join":"join"},"value":["211ventura","211bayarea"]},{"field":"\r\n            dataOwner\r\n            ","operators":{"assert":"assert","join":"join"},"value":["211ventura","211bayarea"]}],"include_total_count":1,"order_by_distance":1,"keyword_is_taxonomy_term":0,"search_within_location_type":"Unknown","facets":["facets","facets"],"search":"food pantry","size":5,"location":"ventura, california","search_fields":["nameService","nameOrganization","descriptionService"],"location_mode":"Within","orderbys":[{"field":"\r\n            nameOrganization\r\n            ","value":""},{"field":"\r\n            nameOrganization\r\n            ","value":""}],"results_advanced":1}

    headers = {
        "data_owners": 'data_owners_example',
        "taxonomy_codes": 'taxonomy_codes_example',
        "taxonomy_terms": 'taxonomy_terms_example',
        "target_terms": 'target_terms_example',
        "tags_service": 'tags_service_example',
        "skip": 56,
        "size": 56,
        "service_area_countries": 'service_area_countries_example',
        "service_area_states": 'service_area_states_example',
        "service_area_counties": 'service_area_counties_example',
        "service_area_cities": 'service_area_cities_example',
        "service_area_postal_codes": 'service_area_postal_codes_example',
        "address_countries": 'address_countries_example',
        "address_states": 'address_states_example',
        "address_counties": 'address_counties_example',
        "address_cities": 'address_cities_example',
        "address_postal_codes": 'address_postal_codes_example',
        "ids": 'ids_example',
        "apiKeyQuery": "special-key",
        "apiKeyHeader": "special-key",
    }
    # uncomment below to make a request
    #response = client.request(
    #    "POST",
    #    "/keyword",
    #    headers=headers,
    #    json=search_input_dto,
    #)

    # uncomment below to assert the status code of the HTTP response
    #assert response.status_code == 200

