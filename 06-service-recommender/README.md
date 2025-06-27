
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

```
cd backend

# Add a prompt template to Phoenix for Haystack pipeline to use
uv run src/bootstrap.py

cd ..
```

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


### 211 Search v2

Get OpenAPI from https://apiportal.211.org/api-details#api=SearchV2&operation=get-keyword-keywords-keywords-location-location

#### OpenAPI Generator

Use https://openapi-generator.tech/ to generate Python stub for MCP server:

```sh
docker run --rm -v $PWD:/local openapitools/openapi-generator-cli generate -i /local/SearchV2.yaml -g python-fastapi -o local/mcp-211-search-v2-service
```

- Well-defined, detailed, and fairly-complete stubs
- Need to add implementation
- Will need to manually handle OpenAPI spec updates

#### openapi-mcp-generator (TypeScript)

Use https://github.com/harsha-iiiv/openapi-mcp-generator to convert "any OpenAPI 3.0+ spec into an MCP-compatible server."

Warning: https://xata.io/blog/built-xata-mcp-server states "It saves time and keeps the API and MCP definitions in sync, avoiding duplicate work. On the other hand, a naïve one-to-one mapping of every endpoint to an MCP tool can overwhelm an LLM. LLMs struggle to choose the right action from so many low-level options, leading to frequent errors or unpredictable calls, especially if several endpoints have similar purposes. ... Instead, we can autogenerate the groundwork from OpenAPI, then curate it. In practice, this means using codegen to produce a set of tool definitions and client calls, then trimming or augmenting the OpenAPI spec that generates the tools to align with real-world usage."
They used [Kubb](https://kubb.dev/plugins/plugin-mcp/).

```sh
openapi-mcp-generator --input SearchV2.json --output openapi-211-search-v2 --transport=streamable-http --port=3000

cd openapi-211-search-v2
npm install
npm run build
npm run start:http
```

Instructions say to "Use the test client to interact with your MCP server" on http://localhost:3000 but I get a "Not Found" response.

#### MCP Python SDK

* https://github.com/modelcontextprotocol/python-sdk
* referring to [Haystack MCP examples](https://github.com/deepset-ai/haystack-core-integrations/tree/main/integrations/mcp/examples)

https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#streamable-http-transport:
> Note: Streamable HTTP transport is superseding SSE transport for production deployments.

```sh
uv run python src/mcp_server.py
```

Useful for MCP inspecting and debugging:
```sh
npx @modelcontextprotocol/inspector
```

```sh
uv run python src/first_mcp.py
```
