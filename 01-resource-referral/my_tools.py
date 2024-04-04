import json
import os
import random
import requests
from langchain.agents import tool
from langchain.prompts import PromptTemplate
import numpy as np
import pandas

from engine import create_llm
from debugging import debug_runnable

TWO_ONE_ONE_BASE_SEARCH_ENDPOINT = "https://api.211.org/search/v1/api"
# TODO: adjust parameters and get LLM to set correct parameters
@tool
def call_211_api(city: str, service_type:str | list[str]) -> str:
    """Calls National 211 API for the given city and service type, such as 'Consumer Services'"""
    print(f"211 args: city={city}; service_type={service_type}")

    return directly_call_211_api(city, service_type)

def directly_call_211_api(city:str, keyword:str | list[str]) -> str:
    if isinstance(keyword, str):
        return get_services_from_211(city, keyword)
    if isinstance(keyword, list):
        api_results_list = []
        for term in keyword:
            api_result = get_services_from_211(city, term)
            result_obj = json.loads(api_result)
            api_results_list.extend(result_obj)
        return json.dumps(api_results_list, indent=2)
    raise ValueError(f"Invalid keyword type: {type(keyword)}")


def get_services_from_211(city:str, keyword:str | list[str]):
    location_endpoint = f"{TWO_ONE_ONE_BASE_SEARCH_ENDPOINT}/Search/Keyword?Keyword={keyword}&Location={city}&Top=10&OrderBy=Relevance&SearchMode=Any&IncludeStateNationalRecords=true&ReturnTaxonomyTermsIfNoResults=false"

    TWO_ONE_ONE_API_KEY = os.environ.get('TWO_ONE_ONE_API_KEY')

    headers = {
        'Accept': 'application/json',
        'Api-Key': TWO_ONE_ONE_API_KEY,
    }

    location_search = requests.get(location_endpoint, headers=headers)
    # From Search: /api/Filters/ServiceAreas?StateProvince=MI, returns []
    try:        
        first_result = location_search.json()["results"][0]["document"]
        # difficult to find param {location_id}, location_id returns dataowner
        location_id = first_result["idLocation"]
        print("211 location_id: " + location_id)
    except Exception:
        print("Failed to get location result")
    try:
        # In Query: /api/Locations/complete/{location_id}, location_id is inconsistent with other queries
        service_list = f"{TWO_ONE_ONE_BASE_SEARCH_ENDPOINT}/ServicesAtLocation?idLocation={location_id}"
        service_search = requests.get(service_list, headers=headers)
        return json.dumps(service_search.json(), indent=2)
    except Exception:
        print("Failed to get services at location")
    return "[]"

# Check for csv file
csv_file = "nyc_referral_csv.csv"
if not os.path.exists(csv_file):
    print(f"Optionally download {csv_file} from google drive: https://drive.google.com/file/d/1YHgJvZCDF5VtTO-AQ4-I3_1jGzrcOHjY/view?usp=sharing")
    input(f"Press Enter to continue without {csv_file}...")

@tool
def query_spreadsheet(city: str, service_type: str | list[str]) -> str:
    """Search spreadsheet for support resources given the city and service type, such as 'Food Assistance'."""
    print("Querying spreadsheet for", service_type, city)
    if not os.path.exists(csv_file):
        print("Returning empty list, as CSV file not found")
        return "[]"

    # base implementation
    df = pandas.read_csv(csv_file)
    separated_locations = city.split(',')
    city_to_search = separated_locations[0]
    query = service_type if isinstance(service_type, str) else '|'.join(service_type)
    print(query)

    results = df.query(f'needs.str.contains("{query}", case=False) & counties_served.str.contains("{city_to_search}", case=False)', engine='python')
    if results.to_numpy().size == 0:
        return "[]"
    
    csv_with_header_to_json = results.replace(np.nan, None).to_dict('records')
    dict_json = json.dumps(csv_with_header_to_json, indent=2)
    
    return dict_json

@tool
def merge_json_results(user_query, result_211_api, result_spreadsheet):
    """Merge JSON results from 211 API and spreadsheet"""
    print("Merging JSON results", type(result_211_api), type(result_spreadsheet))
    print("  user_query:", user_query)
    dict_listA = json.loads(result_211_api)
    dict_listB = json.loads(result_spreadsheet)
    print("Merging JSON results of sizes:", len(dict_listA), len(dict_listB))
    input("Press Enter to continue...")

    deduplicated_dict = _merge_and_deduplicate(dict_listA, dict_listB)

    relevance_agent = create_relevance_agent()
    # A long list of resources confuses the LLM, so sample only 40
    sampled_resources : list[dict] = random.sample(list(deduplicated_dict.values()), min(40, len(deduplicated_dict)))
    formatted_resources = _format_for_prompt(sampled_resources)
    prioritized_list = relevance_agent.invoke({"resources": formatted_resources, "user_query": user_query})
    return prioritized_list

ALTERNATIVE_KEYS = [
    # from spreadsheet
    "id", "alternate_name", "url", "website", "email", "tax_id", 
    # from 211
    "idService", "idOrganization", "name", "alternateName"
    ]
def _merge_and_deduplicate(dict_listA, dict_listB):
    """Merge 2 list of objects, removing duplicates based on object's 'name'.
    If 'name' is not present, use one of ALTERNATIVE_KEYS to deduplicate."""
    merged_dict_list = dict_listA + dict_listB
    deduplicated_dict = {}
    for obj in merged_dict_list:
        if "name" not in obj:
            id_key = next(key for key in ALTERNATIVE_KEYS if key in obj)
            deduplicated_dict[id_key] = obj
            continue

        if obj["name"] not in deduplicated_dict:
            deduplicated_dict[obj["name"]] = obj
            continue

        deduplicated_dict[obj["name"]] = _merge_objects(deduplicated_dict[obj["name"]], obj)
    return deduplicated_dict

def _merge_objects(objA: dict, objB: dict):
    """Merge 2 objects, concatenating values if same key are in both objects"""
    merged_obj = {}
    for key in set().union(objA.keys(), objB.keys()):
        values_list = [str(x) for x in [objA.get(key), objB.get(key)] if x is not None]
        merged_obj[key] = ";; ".join(set(values_list))
    return merged_obj

APPROVED_RESOURCE_NAMES = ["Alpena CAO"]
def _filter_approved(deduplicated_dict):
    """Filter collection to only include approved resource names"""
    for key in list(deduplicated_dict):
        if key not in APPROVED_RESOURCE_NAMES:
            print(f"Removing from deduplicated_dict[{key}]:", deduplicated_dict[key])
            del deduplicated_dict[key]
    return deduplicated_dict

def _format_for_prompt(resources: dict):
    """Format resources for prompt"""
    return "\n".join([f"- {resource['name']} ({resource['phone']}): provides {resource.get('needs')} for counties {resource.get('counties_served')}. {resource.get('description', '')}"
                      for resource in resources])

def create_relevance_agent():
    return (
        _agent_prompt_template()
        | debug_runnable("  Relevance PROMPT")
        | create_llm(model_name="openhermes", settings={"temperature": 0, "top_p": 0.8})
    )

def _agent_prompt_template():
    template = """You are a helpful automated agent that filters and prioritizes benefits services. \
Downselect to less than 10 services total and prioritize the following list of services based on the user's query. \
Include contact information for each service.

List of services:
{resources}

Begin!

User's query: {user_query}
"""
    return PromptTemplate.from_template(template)
