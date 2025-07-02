# OpportunityV1Service

A list of all methods in the `OpportunityV1Service` service. Click on the method name to view detailed information about that method.

| Methods                                                                           | Description                                                                                                                                                                                                                                                                                                           |
| :-------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [create_v1_opportunities_search](#create_v1_opportunities_search)                 | **ALPHA VERSION** This endpoint in its current form is primarily for testing and feedback. Features in this endpoint are still under heavy development, and subject to change. Not for production use. See [Release Phases](https://github.com/github/roadmap?tab=readme-ov-file#release-phases) for further details. |
| [get_v1_opportunities_by_opportunity_id](#get_v1_opportunities_by_opportunity_id) | **ALPHA VERSION** This endpoint in its current form is primarily for testing and feedback. Features in this endpoint are still under heavy development, and subject to change. Not for production use. See [Release Phases](https://github.com/github/roadmap?tab=readme-ov-file#release-phases) for further details. |

## create_v1_opportunities_search

**ALPHA VERSION** This endpoint in its current form is primarily for testing and feedback. Features in this endpoint are still under heavy development, and subject to change. Not for production use. See [Release Phases](https://github.com/github/roadmap?tab=readme-ov-file#release-phases) for further details.

- HTTP Method: `POST`
- Endpoint: `/v1/opportunities/search`

**Parameters**

| Name         | Type                                                                  | Required | Description       |
| :----------- | :-------------------------------------------------------------------- | :------- | :---------------- |
| request_body | [OpportunitySearchRequestV1](../models/OpportunitySearchRequestV1.md) | ❌       | The request body. |

**Return Type**

`OpportunitySearchResponseV1`

**Example Usage Code Snippet**

```python
from simpler_grants_api import SimplerGrantsApi
from simpler_grants_api.models import OpportunitySearchRequestV1

sdk = SimplerGrantsApi(
    api_key="YOUR_API_KEY",
    api_key_header="YOUR_API_KEY_HEADER",
    timeout=10000
)

request_body = OpportunitySearchRequestV1(
    experimental={
        "scoring_rule": "default"
    },
    filters={
        "agency": {
            "one_of": [
                "USAID"
            ]
        },
        "applicant_type": {
            "one_of": [
                "state_governments"
            ]
        },
        "assistance_listing_number": {
            "one_of": [
                "45.149"
            ]
        },
        "award_ceiling": {
            "max": 10000000,
            "min": 10
        },
        "award_floor": {
            "max": 10000,
            "min": 6
        },
        "close_date": {
            "end_date": "end_date",
            "end_date_relative": -317912,
            "start_date": "start_date",
            "start_date_relative": 735955
        },
        "estimated_total_program_funding": {
            "max": 10000000,
            "min": 7
        },
        "expected_number_of_awards": {
            "max": 25,
            "min": 0
        },
        "funding_category": {
            "one_of": [
                "recovery_act"
            ]
        },
        "funding_instrument": {
            "one_of": [
                "cooperative_agreement"
            ]
        },
        "is_cost_sharing": {
            "one_of": [
                True
            ]
        },
        "opportunity_status": {
            "one_of": [
                "forecasted"
            ]
        },
        "post_date": {
            "end_date": "end_date",
            "end_date_relative": -919745,
            "start_date": "start_date",
            "start_date_relative": 787501
        },
        "top_level_agency": {
            "one_of": [
                "USAID"
            ]
        }
    },
    format="json",
    pagination={
        "page_offset": 1,
        "page_size": 25,
        "sort_order": [
            {
                "order_by": "relevancy",
                "sort_direction": "ascending"
            }
        ]
    },
    query="research",
    query_operator="AND"
)

result = sdk.opportunity_v1.create_v1_opportunities_search(request_body=request_body)

print(result)
```

## get_v1_opportunities_by_opportunity_id

**ALPHA VERSION** This endpoint in its current form is primarily for testing and feedback. Features in this endpoint are still under heavy development, and subject to change. Not for production use. See [Release Phases](https://github.com/github/roadmap?tab=readme-ov-file#release-phases) for further details.

- HTTP Method: `GET`
- Endpoint: `/v1/opportunities/{opportunity_id}`

**Parameters**

| Name           | Type | Required | Description |
| :------------- | :--- | :------- | :---------- |
| opportunity_id | int  | ✅       |             |

**Return Type**

`OpportunityGetResponseV1`

**Example Usage Code Snippet**

```python
from simpler_grants_api import SimplerGrantsApi

sdk = SimplerGrantsApi(
    api_key="YOUR_API_KEY",
    api_key_header="YOUR_API_KEY_HEADER",
    timeout=10000
)

result = sdk.opportunity_v1.get_v1_opportunities_by_opportunity_id(opportunity_id=4)

print(result)
```

<!-- This file was generated by liblab | https://liblab.com/ -->
