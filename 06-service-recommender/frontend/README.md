

```
uv venv --python 3.12
source .venv/bin/activate

# Run locally
uvx streamlit run src/main.py

# To run in docker
uv pip compile pyproject.toml -o requirements.txt
docker compose up --build
```