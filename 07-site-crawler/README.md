
## Setup
```
uv sync
uv run playwright install
```

Copy `.env-template` to a `.env` file and populate with your secrets.

## Test
```
uv run crwl https://excelcenterhighschool.org -o markdown
```
