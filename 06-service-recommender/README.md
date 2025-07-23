
## Architecture

* When a user submits a question in the Streamlit UI (`frontend` subfolder), the frontend calls the API (`backend` subfolder) provided by the Hayhooks service.
* Haystack pipelines are registered with the Hayhooks service. Each pipeline is associated with an API endpoint by name, e.g., the pipeine defined in `backend/pipelines/first` can by triggered via a `POST` request to `http://localhost:1416/first/run`.
* During Haystack pipeline execution, traces are sent to the Phoenix observability tool (running as `phoenix` Docker compose service).
* Phoenix persists those traces to a DB (running as `db` Docker compose service).

### Details

* The Streamlit UI is at http://localhost:8501
    * This can be replaced with a different frontend implemnentation.
* The Phoenix UI is at http://localhost:6006
    * and receives tracing data (i.e., OTLP HTTP data) via `http://localhost:6006/v1/traces` (and OTLP gRPC data via `http://localhost:4317`)
* A Haystack pipeline can query Phoenix for prompt templates.
    * Non-engineers can conduct prompt engineering in the Phoenix UI and have the changes be immediately reflected in pipelines that use the prompt template.
* The Hayhooks service listens on port 1416 -- API docs are at http://localhost:1416/docs
    * New pipelines under a folder can be registered dynamically using `hayhooks pipeline deploy-files -n my_pipeline SOME_PIPELINES_FOLDER`
    * Pipelines can be tested using `curl -X 'POST' 'http://localhost:1416/first/run' -H 'accept: application/json' -H 'Content-Type: application/json' -d '{  "question": "Who lives in Paris?" }'` or using the `hayhooks` commandline.
    * The Hayhooks service can be replaced or supplemented with a separate API implementation that [calls the Hayhooks service](https://docs.haystack.deepset.ai/docs/hayhooks#running-programmatically) or runs Haystack pipelines directly.

## Running

### Create `.env` with API keys

Copy `.env-template` to a `.env` file and populate with your secrets. These secrets (e.g., `OPENAI_API_KEY`) are referenced in the `compose.yaml` file and are used by Haystack pipelines to call LLMs.

### Docker Compose

#### First time running
Build and start the Phoenix Docker containers: `docker compose up phoenix --build`

In another terminal, add a prompt template to Phoenix:
```
cd backend

# Add a prompt template to Phoenix for Haystack pipeline to use
uv run src/bootstrap.py

cd ..
```

Terminate everything.

#### Start all containers

Build and start all necessary Docker containers: `docker compose up --build`


### Running outside of Docker containers

The frontend and backend can be run outside of Docker containers if desired.

Install Python and `uv`.

Note the `requirements.txt` files are only for building Docker images. It is created by running `uv pip compile pyproject.toml -o requirements.txt` using dependencies declared in `pyproject.toml`.

Tip: During development, open the `frontend` and `backend` subfolders as different VSCode projects. For each project, have VSCode use the Python interpreter in the respective `.venv` subfolder.

#### Run Streamlit frontend
```
cd frontend
uv sync
uv run streamlit run src/main.py
```

Optionally, run `source .venv/bin/activate` to avoid having to type `uv run` or `uvx`.

#### Run API backend
```
# Export all variables in .env
set -o allexport
source .env

cd backend

# Download Python dependencies
uv sync

# Add a prompt template to Phoenix for Haystack pipeline to use
uv run src/bootstrap.py

# Start Hayhooks service
uvx hayhooks run --additional-python-path .
```

During pipeline development, test a Haystack pipeline before deploying it to Hayhooks.
For example: `uv run src/haystack_rag.py`

## To enable Phoenix authentication

Based on [documentation](https://arize.com/docs/phoenix/self-hosting/features/authentication), set `PHOENIX_SECRET` in `.env` and modify `compose.yaml` as follows.
* Add these environment variables to the `phoenix` service:
```
      - PHOENIX_ENABLE_AUTH=True
      - PHOENIX_SECRET=${PHOENIX_SECRET}
```
* Log into the Phoenix UI at http://localhost:6006 and create an API key
* Add these environment variables to the `backend` service:
```
      - PHOENIX_API_KEY=${PHOENIX_API_KEY}
      - OTEL_EXPORTER_OTLP_HEADERS=${OTEL_EXPORTER_OTLP_HEADERS}
```

## MCP Services

* https://haystack.deepset.ai/integrations/mcp
    - https://github.com/deepset-ai/haystack-core-integrations/tree/main/integrations/mcp/examples
* https://docs.haystack.deepset.ai/docs/mcptool#with-the-agent-component

Run the following in the `mcp_simpler_grants_gov` subfolder.

### MCP Python SDK server (using Streamable HTTP) and Haystack client

* https://github.com/modelcontextprotocol/python-sdk
* referring to [Haystack MCP examples](https://github.com/deepset-ai/haystack-core-integrations/tree/main/integrations/mcp/examples)

https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#streamable-http-transport:
> Note: Streamable HTTP transport is superseding SSE transport for production deployments.

and https://brightdata.com/blog/ai/sse-vs-streamable-http#:~:text=As%20explained%20here%2C%20third%2Dparty,specs%20must%20implement%20Streamable%20HTTP

Start MCP Server:
```sh
uv run python src/mcp_server.py
```

Useful for MCP inspecting and debugging:
```sh
npx @modelcontextprotocol/inspector
```

Run Haystack pipeline:
```sh
cd ../backend
export OPENAI_API_KEY='...'
MCP_SERVER=true uv run python src/first_mcp.py

COMPUTE_YOOM_MCP_SERVER=true uv run python src/first_mcp.py
```

### Simpler Grants.gov API

- Get OpenAPI from https://api.simpler.grants.gov/openapi.json
- Docs at https://api.simpler.grants.gov/docs

In the `mcp_simpler_grants_gov` folder, copy `.env_template` to `.env` and set `SIMPLER_GRANTS_API_KEY`.

### generate_tools_from_openapi (non-streaming)

This creates regular REST endpoints, not Streamable HTTP or SSE, so the MCP inspector isn't relevant.

Also this 

From https://earthkhan.medium.com/turn-your-openapi-in-mcp-server-in-5-minutes-e2859383d0dc
and https://github.com/nafiul-earth/openapi-2-mcpserver/blob/main/ibmcloud-cos-mcp-server/main.py,
add `mcp_server_simpler_grants.py`,

Start MCP Server:
```sh
uv run python src/mcp_server_simpler_grants.py
```
Note only 2 tools are exposed -- see "Convert to SSE-based MCP service" section below.


Quick test: `curl http://localhost:8000/tools`

MCP client test (without any LLM):
```sh
uv run python src/mcp_simpler_grants_client.py
```

### Convert to SSE-based MCP service

Use https://github.com/tadata-org/fastapi_mcp to quickly create MCP service via SSE. Unfortunately, Streamable HTTP is [not available](https://github.com/tadata-org/fastapi_mcp/discussions/142).

```sh
uv run python src/mcp_server_simpler_grants_sse.py
```

Run MCP inspector
```sh
npx @modelcontextprotocol/inspector
```
and connect to http://localhost:8000/mcp.

However since the `generate_tools_from_openapi` approach was used, only 2 generic tools are listed:
- `list_tools_tools_get`
- `invoke_tool_invoke_post`


### Convert to Streamable HTTP transport protocol

> MCP (Model Context Protocol) can use non-streamable HTTP, but it's not the preferred or recommended approach. While older versions of MCP relied heavily on Server-Sent Events (SSE) for streaming data, the current specification favors Streamable HTTP. Streamable HTTP allows for a more efficient and stateless way to communicate with MCP servers, making it the preferred method for new implementations. 

#### (Recommended) jlowin's FastMCP

(Not to be confused with MCP Python SDK which uses the `mcp.server.fastmcp` package.)

Use https://github.com/jlowin/fastmcp (version 2.10.4), specifically https://gofastmcp.com/servers/openapi#openapi-integration.

> FastMCP can automatically generate an MCP server from an OpenAPI specification or FastAPI app. Instead of manually creating tools and resources, you provide an OpenAPI spec and FastMCP intelligently converts your API endpoints into the appropriate MCP components.

Start MCP Server:
```sh
uv run python src/mcp_server_simpler_grants_streamable.py
```

- Had to remove `  "servers": "."` from json to address `OpenAPI schema validation failed`
- Had to remove extra `"null"` under `schema['$defs']['OpportunityV1']['properties']['category']['type']` in json to address `['string', 'null', 'null'] is not valid under any of the given schemas`

Run MCP inspector
```sh
npx @modelcontextprotocol/inspector
```
and connect to http://localhost:8000/mcp using Streamable HTTP transport protocol and list tools.

- Select `Health` tool and "Run Tool"
- Select `Opportunity_Search` tool and 
   - paste [this snippet](https://api.simpler.grants.gov/docs#/Opportunity%20v1/post_v1_opportunities_search) into the `pagination` text area:
```json
{
    "page_offset": 1,
    "page_size": 25
}
```
   - and some search term like `NASA` into the `query` text area. Then click "Run Tool".

### jlowin's FastMCP and Haystack client

Start MCP Server:
```sh
uv run python src/mcp_server_simpler_grants_streamable.py
```

Run Haystack pipeline:
```sh
cd ../backend
export OPENAI_API_KEY='...'
GRANTS_MCP_SERVER=true uv run python src/first_mcp.py
```

Results in error: `Output validation error: None is not of type 'string'`

#### LLM errors due to JSON Schema (generated from the OpenAPI spec)

Got "Invalid schema" error and "Please ensure it is a valid JSON Schema." message.
- No responses to this post: https://community.openai.com/t/tool-calls-rejecting-valid-json-from-correct-specification/862849
- https://community.openai.com/t/pydantic-response-model-failure/789207:
    - Is the input too large for your max tokens maybe?
    - If I make my response model too “deep” it seems to fail.
    - Not the problem: "Replace #/definitions with #$defs"
    - Found a "Circular References" to AgencyV1

It frequently doesn't provide required 'pagination' parameter, so added `Make sure to provide the required 'pagination' parameter.` to the LLM prompt.

Haystack's ToolInvoker may not handle OpenAI API versions beyond v3.0:
- v3.0: The nullable: true keyword is used for object properties that can be null.
- v3.1: Instead of nullable: true, you can include null as one of the possible types in the type array.

The OpenAPI spec for simpler.grants.gov's is v3.1 so this version incompatibility also causes:
- "Output validation error: None is not of type 'string'" due to incorrect use of 'one_of' in the OpenAPI spec
- "Input validation error: ['NASA'] is not of type 'object'" due to `"type": [ "object" ]` in the OpenAPI spec

Tried https://github.com/apiture/openapi-down-convert to downgrade the version:

Validating v3.1:
```
❯ uv run --with openapi-spec-validator openapi-spec-validator simpler_grants_gov-openapi_v3_1.json
simpler_grants_gov-openapi_v3_1.json: OK
```

Validating v3.0 fails:
```
❯ uv run --with openapi-spec-validator openapi-spec-validator simpler_grants_gov-openapi_v3.json
- Failed validating 'oneOf' ...
```
so the downgrade wasn't successful.

### Concluding remarks

There are several factors that make it challenging:
- The OpenAPI spec from Simpler Grants is not stable (it’s an ALPHA VERSION) so it’s uncertain how polished the spec is – this is evidenced by me having to tweak the JSON file so that the MCP server starts up without errors.
- The API is fairly large, so trying to pinpoint the actual root cause of the error is challenging.
- There are many OpenAI forum threads for `invalid_request_error` and there are multiple possible causes. The OpenAPI spec is interpreted by several libraries (jlowin's FastMCP, indirectly by Haystack's ToolInvoker, and the LLM that generate the API call). A malformed JSON representation or OpenAPI spec version incompatibility could result in an error.

Possible workarounds for complex OpenAPI specs:
- To use jlowin's FastMCP, winnow down the API json so that it's smaller and simpler, reducing the possibility of errors and hallucinations.
- Use a proxy MCP service that acts like `mcp_simpler_grants_client.py` so that it provides a minimal API spec for the MCP client.
- Some other way to override the JSON schema so that it’s compatible with OpenAI’s acceptable schema – https://community.openai.com/t/pydantic-response-model-failure/789207 
   - "If I make my response model too "deep" it seems to fail." 
   - "I see, GPT says there are some issues with the actual schema: ChatGPT, might want to take a look. There are various versions of JSON schema"

The more parameters and options there are in the API spec, the more uncertainty and risk (1) when developing the MCP server and client, and (2) when the LLM generates tool-calling output.
