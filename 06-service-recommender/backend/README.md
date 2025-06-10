```
uv venv --python 3.12
uv init
source .venv/bin/activate
```

```
uv add haystack-ai
uv add arize-phoenix-otel
uv add openinference-instrumentation-haystack
uv add python-dotenv
uv add openai
```

```
# To run in docker
uv pip compile pyproject.toml -o requirements.txt
docker compose up --build
```

```
# https://github.com/deepset-ai/hayhooks/tree/main/examples/shared_code_between_wrappers#option-3-launch-hayhooks-with-the---additional-python-path-flag
hayhooks run --additional-python-path . &

# Deploy all pipeline files from a directory to the Hayhooks server.
hayhooks pipeline deploy-files -n my_pipeline hayhooks_pipelines
hayhooks status
```

- input pipeline source files
- output serialized pipelines

```
hayhooks pipeline deploy-files -n my_pipeline --overwrite --skip-saving-files hayhooks_pipelines

curl -X 'POST' 'http://localhost:1416/my_pipeline/run' -H 'accept: application/json' -H 'Content-Type: application/json' -d '{  "question": "Who lives in Paris?" }'
```