import json
import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
import os

from dotenv import load_dotenv

load_dotenv()

OPENAPI_JSON = "simpler_grants_gov-openapi.json"
BASE_URL = "https://api.simpler.grants.gov"


app = FastAPI()

# In-memory registry of tools
tool_registry = {}


@app.on_event("startup")
async def startup():
    if os.path.exists(OPENAPI_JSON):
        with open(OPENAPI_JSON, "r", encoding="utf-8") as f:
            openapi = json.load(f)
    else:
        openapi = await fetch_openapi_spec()
    generate_tools_from_openapi(openapi)
    print(f"Registered tools: {list(tool_registry.keys())}")


async def fetch_openapi_spec():
    print("Fetching OpenAPI spec from Simpler Grants API...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/openapi.json")
        response.raise_for_status()
        return response.json()


@app.get("/tools")
async def list_tools():
    return JSONResponse(content={"tools": list(tool_registry.keys())})


class ToolCallInput(BaseModel):
    tool_name: str
    input: Dict[str, Any]


@app.post("/invoke")
async def invoke_tool(call: ToolCallInput):
    tool_name = call.tool_name
    input_data = call.input
    print("input_data", input_data)
    if tool_name not in tool_registry:
        return JSONResponse(status_code=404, content={"error": "Tool not found"})

    tool_func = tool_registry[tool_name]
    try:
        result = await tool_func(input_data)
        return JSONResponse(content={"output": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# From https://earthkhan.medium.com/turn-your-openapi-in-mcp-server-in-5-minutes-e2859383d0dc
def generate_tools_from_openapi(openapi: Dict[str, Any]):
    paths = openapi.get("paths", {})
    if not paths:
        raise ValueError(f"Path is empty or invalid: {openapi}")

    for path, methods in paths.items():
        for method, details in methods.items():
            operation_id = (
                details.get("operationId") or f"{method}_{path.replace('/', '_')}"
            )
            summary = details.get("summary", "")
            print("operation_id:", operation_id)
            print("summary:", summary)

            # Create a basic tool function with a name and HTTP method
            def make_tool(p, m):
                print(f"Creating tool for {m.upper()} {p}")
                async def tool_func(input_data):
                    try:
                        # region = input_data.get("region", "us-south")
                        headers = input_data.get("headers", {})
                        body = input_data.get("body", None)
                        params = input_data.get("params", {})
                        print("params:", params)
                        formatted_path = p
                        print("formatted_path:", formatted_path)
                        for key, value in params.items():
                            formatted_path = formatted_path.replace(f"{{{key}}}", value)
                        # url = f"https://s3.{region}.cloud-object-storage.appdomain.cloud{formatted_path}"
                        url = f"{BASE_URL}{formatted_path}"
                        print("URL:", url)
                        async with httpx.AsyncClient() as client:
                            req = client.build_request(
                                m.upper(), url, headers=headers, json=body, params=params
                            )
                            res = await client.send(req)
                            return {"status_code": res.status_code, "body": res.text}
                    except Exception as e:
                        print(f"Error invoking tool {p}: {e}")
                        raise e

                return tool_func

            tool_registry[operation_id] = make_tool(path, method)


if __name__ == "__main__":
    uvicorn.run("mcp_server_simpler_grants:app", host="0.0.0.0", port=8000, reload=True)
