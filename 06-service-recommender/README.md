
## Architecture

* Streamlit UI (`frontend` subfolder) calls API (`backend` subfolder) of deployed Haystack pipelines (called Hayhooks)
* Hayhooks sends traces to Phoenix
* Phoenix (`phoenix` Docker compose service) persists those traces to DB (`db` Docker compose service)

### Details

* A Haystack pipeline can query Phoenix for prompt templates
* Streamlit UI is at http://localhost:8501/
* Phoenix UI is at http://localhost:6006
   * and receives tracing data (i.e., OTLP HTTP data) via http://localhost:6006/v1/traces (and OTLP gRPC data via http://localhost:4317)
* Hayhooks service listens on port 1416
    * New pipelines can be registered
    * Pipelines can be tested using `curl -X 'POST' 'http://localhost:1416/first/run' -H 'accept: application/json' -H 'Content-Type: application/json' -d '{  "question": "Who lives in Paris?" }'`

## Running

### Create `backend/.env`

In the `backend` subfolder, copy `.env-template` to a `.env` file and populate with your secrets. These secrets (e.g., `OPENAI_API_KEY`) are referenced in the `compose.yaml` file.

### Docker Compose

`docker compose up --build`
