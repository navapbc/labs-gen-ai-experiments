import json

# import httpx
# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel
# from typing import Dict, Any
# import uvicorn
import os

import httpx
from fastmcp import FastMCP

from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ["SIMPLER_GRANTS_API_KEY"]

OPENAPI_JSON = "simpler_grants_gov-openapi.json"
BASE_URL = "https://api.simpler.grants.gov"

# Create an HTTP client for your API
client = httpx.AsyncClient(
    base_url=BASE_URL, headers={"X-Auth": API_KEY}
)

# Load your OpenAPI spec
if os.path.exists(OPENAPI_JSON):
    with open(OPENAPI_JSON, "r", encoding="utf-8") as f:
        openapi_spec = json.load(f)
else:
    print("Fetching OpenAPI spec from Simpler Grants API...")
    openapi_spec = httpx.get(f"{BASE_URL}/openapi.json").json()

# Create the MCP server
mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec, client=client, name="My API Server"
)

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/mcp")
