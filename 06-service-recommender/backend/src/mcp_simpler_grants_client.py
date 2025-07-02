import requests
import os
import json
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["SIMPLER_GRANTS_API_KEY"]
MCP_URL = os.environ["MCP_URL"]


# def get_iam_token():
#     iam_url = "https://.../identity/token"
#     headers = {
#         "Content-Type": "application/x-www-form-urlencoded",
#     }
#     data = {
#         "apikey": API_KEY,
#         "grant_type": "urn:...:params:oauth:grant-type:apikey"
#     }
#     response = requests.post(iam_url, headers=headers, data=data)
#     response.raise_for_status()
#     return response.json()["access_token"]


def get__health():
    tool_call = {
        "tool_name": "get__health",
        "input": {        },
    }
    response = requests.post(MCP_URL, json=tool_call)
    print("get__health:", response.json())
    print_response(response)

def print_response(response):
    output = response.json()["output"]
    # pprint(output["body"])
    body = json.loads(output["body"])
    pprint(body)


def search_opportunities(query):
    tool_call = {
        "tool_name": "post__v1_opportunities_search",
        "input": {
            "headers": {
                "X-Auth": API_KEY,
            },
            "body": {
                "pagination": {
                    "page_offset": 1,
                    "page_size": 25,
                    "sort_order": [
                        {"order_by": "opportunity_id", "sort_direction": "ascending"}
                    ],
                },
                "query": query,
            },
        },
    }
    response = requests.post(MCP_URL, json=tool_call)
    print(f"Search Opportunities '{query}':", response.json())
    print_response(response)


def get_opportunity(opportunity_id):
    tool_call = {
        "tool_name": "get__v1_opportunities_{opportunity_id}",
        "input": {
            "headers": {
                "X-Auth": API_KEY,
            },
            "params": {
                "opportunity_id": opportunity_id,
            },
        },
    }
    response = requests.post(MCP_URL, json=tool_call)
    print(f"Get Opportunity '{opportunity_id}':", response.json())
    print_response(response)

if __name__ == "__main__":
    # get__health()
    # search_opportunities("Artificial Intelligence")
    get_opportunity("315583")
