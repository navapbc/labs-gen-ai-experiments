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