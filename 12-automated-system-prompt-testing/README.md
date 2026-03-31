# Experiment 12: Automated System Prompt A/B Testing

Test and compare system prompt versions automatically. Given a baseline prompt and one or more modified prompts, this tool:

1. **Simulates** — Runs all versions through a fixed test corpus via OpenAI API
2. **Evaluates** — Scores outputs on up to 8 configurable quality dimensions
3. **Compares** — Generates a markdown report with pairwise wins, flag counts, and regressions

Also includes a **web UI** with Phoenix integration for interactive testing.

## Quickstart

```bash
# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key
cp .env.example .env
# Edit .env with your key

# Run with sample data (dry-run — no API calls)
python prompt_test.py run --config sample_data/config.yaml --dry-run

# Run for real (requires OPENAI_API_KEY)
python prompt_test.py run --config sample_data/config.yaml
```

The comparison report will be saved to `results/comparison_report.md`.

## How It Works

### Step 1: Simulate (`simulate.py`)

For each query in the test corpus, renders each prompt template with the query variables and calls the OpenAI API. Saves raw outputs with parsed JSON and extracted resources.

### Step 2: Evaluate (`evaluate.py`)

Runs configurable quality dimensions on each version's output:

| Dimension | What It Checks | Flag Examples |
|-----------|---------------|---------------|
| `output_structure` | Valid JSON with expected keys | `INVALID_JSON`, `ZERO_RESOURCES` |
| `resource_count` | Resource count within bounds | `TOO_FEW_RESOURCES`, `EXCESSIVE_RESOURCES` |
| `url_validity` | HTTP HEAD on resource URLs | `BROKEN_URL`, `HOMEPAGE_ONLY` |
| `readability` | Flesch-Kincaid grade level | `ABOVE_8TH_GRADE` |
| `duplicates` | Fuzzy name/address matching | `DUPLICATE_RESOURCE` |
| `contact_completeness` | Phone/address presence | `MISSING_CONTACT_N` |
| `rag_grounding` | Output vs input context match | `UNGROUNDED_RESOURCE` |
| `location_match` | Geographic consistency | `CROSS_STATE` |

### Step 3: Compare (`compare.py`)

Generates a markdown report with:
- Executive summary (pairwise win/loss/tie counts)
- Overall metrics table (valid JSON rate, avg resources, avg flags)
- Per-dimension comparison (duplicates, readability, grounding, URLs, etc.)
- Per-query results table
- Regression analysis (queries where the new version is worse)

## Configuration

Copy `config.example.yaml` and customize:

```yaml
simulation:
  versions:
    - name: baseline
      template_path: prompts/v1.txt
    - name: improved
      template_path: prompts/v2.txt
  test_corpus_path: my_test_queries.json
  model: gpt-4o
  temperature: 0.7

evaluation:
  resource_path: resources  # JSONPath to resources in output
  dimensions:
    readability: { enabled: true, max_grade_level: 8.0 }
    url_validity: { enabled: true, skip_validation: false }
    # ... see config.example.yaml for all options
```

### Test Corpus Format

JSON array of query objects:

```json
[
  {
    "id": "query_001",
    "query": "The user's question or request text",
    "location": "City, State ZIP",
    "resources_context": "RAG context that was provided to the LLM",
    "categories": ["food", "housing"]
  }
]
```

### Prompt Templates

Use Jinja2 syntax for variable substitution:

```
You are a helpful assistant.

## Query
{{ query }}

## Available Resources
{{ resources_context }}
```

Available variables: `query`, `location`, `resources_context`, `categories`, plus any extra fields from your test corpus entries.

## Phoenix Integration

Pull your production prompt directly from Phoenix as the baseline, and deploy winning variants back.

### Setup

Add Phoenix credentials to `.env`:

```
PHOENIX_URL=https://phoenix.your-instance.com:6006
PHOENIX_API_KEY=your-api-key
```

### Using Phoenix as a prompt source (CLI)

In your config YAML, set `source: phoenix` on a version:

```yaml
simulation:
  versions:
    - name: production
      source: phoenix
      prompt_name: generate_referrals_centraltx
      version: latest    # or a specific number
      template_format: plain
    - name: variant
      template_path: prompts/my_variant.txt
```

### Web UI

Launch the browser-based UI for interactive testing:

```bash
python prompt_test.py web --port 5001
```

The web UI lets you:
- Browse Phoenix prompts and load any version as baseline
- Edit a variant in a side-by-side editor
- Configure model, temperature, test corpus, and evaluation dimensions
- Run A/B tests and view the comparison report inline
- Deploy winning variants back to Phoenix

## CLI Reference

```bash
# Run all steps
python prompt_test.py run --config config.yaml

# Run all steps (dry-run, no API calls)
python prompt_test.py run --config config.yaml --dry-run

# Run individual steps
python prompt_test.py simulate --config config.yaml --limit 3
python prompt_test.py evaluate --config config.yaml --skip-urls
python prompt_test.py compare --config config.yaml

# Launch web UI
python prompt_test.py web
python prompt_test.py web --port 8080 --no-browser
```

## Adapting for Your Use Case

1. **Write your prompt templates** — Put your baseline and improved prompts in files, using `{{ variable }}` syntax for dynamic content
2. **Create your test corpus** — JSON array with queries that exercise your prompts. Include RAG context if your system uses it
3. **Configure dimensions** — Enable/disable quality checks and set thresholds in your YAML config
4. **Set `resource_path`** — If your output JSON nests resources differently (e.g., `data.items` instead of `resources`), update this in config
5. **Run and iterate** — Use the comparison report to identify regressions and guide prompt improvements
