# UserV1InternalOnlyService

A list of all methods in the `UserV1InternalOnlyService` service. Click on the method name to view detailed information about that method.

| Methods                                                                                                                               | Description                                                                                                                                                                                                                                                                                                                                |
| :------------------------------------------------------------------------------------------------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [get_v1_users_login](#get_v1_users_login)                                                                                             | To use this endpoint, click [this link](/v1/users/login) which will redirect you to an OAuth provider where you can sign into an account. Do not try to use the execute option below as OpenAPI will not redirect your browser for you. The token you receive can then be set to the X-SGG-Token header for authenticating with endpoints. |
| [create_v1_users_token_logout](#create_v1_users_token_logout)                                                                         |                                                                                                                                                                                                                                                                                                                                            |
| [create_v1_users_token_refresh](#create_v1_users_token_refresh)                                                                       |                                                                                                                                                                                                                                                                                                                                            |
| [get_v1_users_by_user_id](#get_v1_users_by_user_id)                                                                                   |                                                                                                                                                                                                                                                                                                                                            |
| [get_v1_users_by_user_id_organizations](#get_v1_users_by_user_id_organizations)                                                       |                                                                                                                                                                                                                                                                                                                                            |
| [create_v1_users_by_user_id_saved_opportunities](#create_v1_users_by_user_id_saved_opportunities)                                     |                                                                                                                                                                                                                                                                                                                                            |
| [create_v1_users_by_user_id_saved_opportunities_list](#create_v1_users_by_user_id_saved_opportunities_list)                           |                                                                                                                                                                                                                                                                                                                                            |
| [delete_v1_users_by_user_id_saved_opportunities_by_opportunity_id](#delete_v1_users_by_user_id_saved_opportunities_by_opportunity_id) |                                                                                                                                                                                                                                                                                                                                            |
| [create_v1_users_by_user_id_saved_searches](#create_v1_users_by_user_id_saved_searches)                                               |                                                                                                                                                                                                                                                                                                                                            |
| [create_v1_users_by_user_id_saved_searches_list](#create_v1_users_by_user_id_saved_searches_list)                                     |                                                                                                                                                                                                                                                                                                                                            |
| [update_v1_users_by_user_id_saved_searches_by_saved_search_id](#update_v1_users_by_user_id_saved_searches_by_saved_search_id)         |                                                                                                                                                                                                                                                                                                                                            |
| [delete_v1_users_by_user_id_saved_searches_by_saved_search_id](#delete_v1_users_by_user_id_saved_searches_by_saved_search_id)         |                                                                                                                                                                                                                                                                                                                                            |

## get_v1_users_login

To use this endpoint, click [this link](/v1/users/login) which will redirect you to an OAuth provider where you can sign into an account. Do not try to use the execute option below as OpenAPI will not redirect your browser for you. The token you receive can then be set to the X-SGG-Token header for authenticating with endpoints.

- HTTP Method: `GET`
- Endpoint: `/v1/users/login`

**Return Type**

`any`

**Example Usage Code Snippet**

```python
from simpler_grants_api import SimplerGrantsApi

sdk = SimplerGrantsApi(
    api_key="YOUR_API_KEY",
    api_key_header="YOUR_API_KEY_HEADER",
    timeout=10000
)

result = sdk.user_v1_internal_only.get_v1_users_login()

print(result)
```

## create_v1_users_token_logout

- HTTP Method: `POST`
- Endpoint: `/v1/users/token/logout`

**Return Type**

`UserTokenLogoutResponse`

**Example Usage Code Snippet**

```python
from simpler_grants_api import SimplerGrantsApi

sdk = SimplerGrantsApi(
    api_key="YOUR_API_KEY",
    api_key_header="YOUR_API_KEY_HEADER",
    timeout=10000
)

result = sdk.user_v1_internal_only.create_v1_users_token_logout()

print(result)
```

## create_v1_users_token_refresh

- HTTP Method: `POST`
- Endpoint: `/v1/users/token/refresh`

**Return Type**

`UserTokenRefreshResponse`

**Example Usage Code Snippet**

```python
from simpler_grants_api import SimplerGrantsApi

sdk = SimplerGrantsApi(
    api_key="YOUR_API_KEY",
    api_key_header="YOUR_API_KEY_HEADER",
    timeout=10000
)

result = sdk.user_v1_internal_only.create_v1_users_token_refresh()

print(result)
```

## get_v1_users_by_user_id

- HTTP Method: `GET`
- Endpoint: `/v1/users/{user_id}`

**Parameters**

| Name    | Type | Required | Description |
| :------ | :--- | :------- | :---------- |
| user_id | str  | ✅       |             |

**Return Type**

`UserGetResponse`

**Example Usage Code Snippet**

```python
from simpler_grants_api import SimplerGrantsApi

sdk = SimplerGrantsApi(
    api_key="YOUR_API_KEY",
    api_key_header="YOUR_API_KEY_HEADER",
    timeout=10000
)

result = sdk.user_v1_internal_only.get_v1_users_by_user_id(user_id="user_id")

print(result)
```

## get_v1_users_by_user_id_organizations

- HTTP Method: `GET`
- Endpoint: `/v1/users/{user_id}/organizations`

**Parameters**

| Name    | Type | Required | Description |
| :------ | :--- | :------- | :---------- |
| user_id | str  | ✅       |             |

**Return Type**

`UserOrganizationsResponse`

**Example Usage Code Snippet**

```python
from simpler_grants_api import SimplerGrantsApi

sdk = SimplerGrantsApi(
    api_key="YOUR_API_KEY",
    api_key_header="YOUR_API_KEY_HEADER",
    timeout=10000
)

result = sdk.user_v1_internal_only.get_v1_users_by_user_id_organizations(user_id="user_id")

print(result)
```

## create_v1_users_by_user_id_saved_opportunities

- HTTP Method: `POST`
- Endpoint: `/v1/users/{user_id}/saved-opportunities`

**Parameters**

| Name         | Type                                                                  | Required | Description       |
| :----------- | :-------------------------------------------------------------------- | :------- | :---------------- |
| request_body | [UserSaveOpportunityRequest](../models/UserSaveOpportunityRequest.md) | ❌       | The request body. |
| user_id      | str                                                                   | ✅       |                   |

**Return Type**

`UserSaveOpportunityResponse`

**Example Usage Code Snippet**

```python
from simpler_grants_api import SimplerGrantsApi
from simpler_grants_api.models import UserSaveOpportunityRequest

sdk = SimplerGrantsApi(
    api_key="YOUR_API_KEY",
    api_key_header="YOUR_API_KEY_HEADER",
    timeout=10000
)

request_body = UserSaveOpportunityRequest(
    opportunity_id=2
)

result = sdk.user_v1_internal_only.create_v1_users_by_user_id_saved_opportunities(
    request_body=request_body,
    user_id="user_id"
)

print(result)
```

## create_v1_users_by_user_id_saved_opportunities_list

- HTTP Method: `POST`
- Endpoint: `/v1/users/{user_id}/saved-opportunities/list`

**Parameters**

| Name         | Type                                                                        | Required | Description       |
| :----------- | :-------------------------------------------------------------------------- | :------- | :---------------- |
| request_body | [UserSavedOpportunitiesRequest](../models/UserSavedOpportunitiesRequest.md) | ❌       | The request body. |
| user_id      | str                                                                         | ✅       |                   |

**Return Type**

`UserSavedOpportunitiesResponse`

**Example Usage Code Snippet**

```python
from simpler_grants_api import SimplerGrantsApi
from simpler_grants_api.models import UserSavedOpportunitiesRequest

sdk = SimplerGrantsApi(
    api_key="YOUR_API_KEY",
    api_key_header="YOUR_API_KEY_HEADER",
    timeout=10000
)

request_body = UserSavedOpportunitiesRequest(
    pagination={
        "page_offset": 1,
        "page_size": 25,
        "sort_order": [
            {
                "order_by": "created_at",
                "sort_direction": "ascending"
            }
        ]
    }
)

result = sdk.user_v1_internal_only.create_v1_users_by_user_id_saved_opportunities_list(
    request_body=request_body,
    user_id="user_id"
)

print(result)
```

## delete_v1_users_by_user_id_saved_opportunities_by_opportunity_id

- HTTP Method: `DELETE`
- Endpoint: `/v1/users/{user_id}/saved-opportunities/{opportunity_id}`

**Parameters**

| Name           | Type | Required | Description |
| :------------- | :--- | :------- | :---------- |
| user_id        | str  | ✅       |             |
| opportunity_id | int  | ✅       |             |

**Return Type**

`UserDeleteSavedOpportunityResponse`

**Example Usage Code Snippet**

```python
from simpler_grants_api import SimplerGrantsApi

sdk = SimplerGrantsApi(
    api_key="YOUR_API_KEY",
    api_key_header="YOUR_API_KEY_HEADER",
    timeout=10000
)

result = sdk.user_v1_internal_only.delete_v1_users_by_user_id_saved_opportunities_by_opportunity_id(
    user_id="user_id",
    opportunity_id=4
)

print(result)
```

## create_v1_users_by_user_id_saved_searches

- HTTP Method: `POST`
- Endpoint: `/v1/users/{user_id}/saved-searches`

**Parameters**

| Name         | Type                                                        | Required | Description       |
| :----------- | :---------------------------------------------------------- | :------- | :---------------- |
| request_body | [UserSaveSearchRequest](../models/UserSaveSearchRequest.md) | ❌       | The request body. |
| user_id      | str                                                         | ✅       |                   |

**Return Type**

`UserSaveSearchResponse`

**Example Usage Code Snippet**

```python
from simpler_grants_api import SimplerGrantsApi
from simpler_grants_api.models import UserSaveSearchRequest

sdk = SimplerGrantsApi(
    api_key="YOUR_API_KEY",
    api_key_header="YOUR_API_KEY_HEADER",
    timeout=10000
)

request_body = UserSaveSearchRequest(
    name="Example search",
    search_query={
        "experimental": {
            "scoring_rule": "default"
        },
        "filters": {
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
        "format": "json",
        "pagination": {
            "page_offset": 1,
            "page_size": 25,
            "sort_order": [
                {
                    "order_by": "relevancy",
                    "sort_direction": "ascending"
                }
            ]
        },
        "query": "research",
        "query_operator": "AND"
    }
)

result = sdk.user_v1_internal_only.create_v1_users_by_user_id_saved_searches(
    request_body=request_body,
    user_id="user_id"
)

print(result)
```

## create_v1_users_by_user_id_saved_searches_list

- HTTP Method: `POST`
- Endpoint: `/v1/users/{user_id}/saved-searches/list`

**Parameters**

| Name         | Type                                                              | Required | Description       |
| :----------- | :---------------------------------------------------------------- | :------- | :---------------- |
| request_body | [UserSavedSearchesRequest](../models/UserSavedSearchesRequest.md) | ❌       | The request body. |
| user_id      | str                                                               | ✅       |                   |

**Return Type**

`UserSavedSearchesResponse`

**Example Usage Code Snippet**

```python
from simpler_grants_api import SimplerGrantsApi
from simpler_grants_api.models import UserSavedSearchesRequest

sdk = SimplerGrantsApi(
    api_key="YOUR_API_KEY",
    api_key_header="YOUR_API_KEY_HEADER",
    timeout=10000
)

request_body = UserSavedSearchesRequest(
    pagination={
        "page_offset": 1,
        "page_size": 25,
        "sort_order": [
            {
                "order_by": "created_at",
                "sort_direction": "ascending"
            }
        ]
    }
)

result = sdk.user_v1_internal_only.create_v1_users_by_user_id_saved_searches_list(
    request_body=request_body,
    user_id="user_id"
)

print(result)
```

## update_v1_users_by_user_id_saved_searches_by_saved_search_id

- HTTP Method: `PUT`
- Endpoint: `/v1/users/{user_id}/saved-searches/{saved_search_id}`

**Parameters**

| Name            | Type                                                                      | Required | Description       |
| :-------------- | :------------------------------------------------------------------------ | :------- | :---------------- |
| request_body    | [UserUpdateSavedSearchRequest](../models/UserUpdateSavedSearchRequest.md) | ❌       | The request body. |
| user_id         | str                                                                       | ✅       |                   |
| saved_search_id | str                                                                       | ✅       |                   |

**Return Type**

`UserUpdateSavedSearchResponse`

**Example Usage Code Snippet**

```python
from simpler_grants_api import SimplerGrantsApi
from simpler_grants_api.models import UserUpdateSavedSearchRequest

sdk = SimplerGrantsApi(
    api_key="YOUR_API_KEY",
    api_key_header="YOUR_API_KEY_HEADER",
    timeout=10000
)

request_body = UserUpdateSavedSearchRequest(
    name="Example search"
)

result = sdk.user_v1_internal_only.update_v1_users_by_user_id_saved_searches_by_saved_search_id(
    request_body=request_body,
    user_id="user_id",
    saved_search_id="saved_search_id"
)

print(result)
```

## delete_v1_users_by_user_id_saved_searches_by_saved_search_id

- HTTP Method: `DELETE`
- Endpoint: `/v1/users/{user_id}/saved-searches/{saved_search_id}`

**Parameters**

| Name            | Type | Required | Description |
| :-------------- | :--- | :------- | :---------- |
| user_id         | str  | ✅       |             |
| saved_search_id | str  | ✅       |             |

**Return Type**

`UserDeleteSavedSearchResponse`

**Example Usage Code Snippet**

```python
from simpler_grants_api import SimplerGrantsApi

sdk = SimplerGrantsApi(
    api_key="YOUR_API_KEY",
    api_key_header="YOUR_API_KEY_HEADER",
    timeout=10000
)

result = sdk.user_v1_internal_only.delete_v1_users_by_user_id_saved_searches_by_saved_search_id(
    user_id="user_id",
    saved_search_id="saved_search_id"
)

print(result)
```

<!-- This file was generated by liblab | https://liblab.com/ -->
