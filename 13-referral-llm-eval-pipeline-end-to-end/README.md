# Experiment 13: Referral LLM Evaluation & Optimization Pipeline

A pipeline for evaluating and optimizing LLM-generated resource referrals. Given access to a Phoenix observability instance (or trace data), it extracts traces, runs automated quality checks across 8 dimensions, performs statistical analysis, generates improvement recommendations, and can automatically iterate on prompts until quality targets are met.

> **Scope:** This pipeline is purpose-built for **resource referral systems** — LLMs that recommend community services (food banks, shelters, legal aid, etc.) to people in need. The evaluation dimensions, fix strategies, and optimization logic encode domain-specific knowledge from the v48-v53 prompt iteration cycle. For a generalized version applicable to other GenAI products, see the [Generalizing Beyond Referrals](#generalizing-beyond-referrals) section.

## Quickstart

```bash
# Install dependencies
pip install -r requirements.txt

# Run all phases on sample data (no API keys needed)
python pipeline.py run --config sample_data/config.yaml
```

This runs phases 1-5 on 20 bundled sample traces and produces:
- `results/traces.json` — Extracted trace data
- `results/eval_results.json` — Automated evaluation results
- `results/sample.json` — Stratified sample selection
- `results/eval_report.md` — Statistical analysis report
- `results/recommendations.md` — Prioritized improvement recommendations

## Pipeline Phases

| Phase | Command | What It Does |
|-------|---------|-------------|
| 1. Extract | `pipeline.py extract` | Pull traces from Phoenix API or sample data |
| 2. Evaluate | `pipeline.py evaluate` | Run 8 automated quality dimensions on all traces |
| 3. Sample | `pipeline.py sample` | Stratified sampling for deep review |
| 4. Analyze | `pipeline.py analyze` | Statistical analysis with 95% confidence intervals |
| 5. Improve | `pipeline.py improve` | Map error patterns to prompt improvement strategies |
| 6. Iterate | `pipeline.py iterate` | A/B test prompt changes (requires OpenAI API) |
| **Optimize** | `pipeline.py optimize` | **Automated loop: evaluate → improve → test → repeat** |
| **Deploy** | `pipeline.py deploy` | **Push a prompt to Phoenix** |

Run all phases: `python pipeline.py run --config config.yaml`

Run individual phases: `python pipeline.py evaluate --config config.yaml`

### Automated Optimization

The `optimize` command closes the loop — it loads a referral prompt, evaluates it against a test corpus, uses an LLM to generate an improved variant using proven referral-specific fix strategies, A/B tests both, and repeats until quality targets are met:

```bash
python pipeline.py optimize --config config.yaml
```

The loop stops when any of these are true:
- Total flags across all test queries <= `flag_threshold` (default: 2)
- No improvement found (variant doesn't beat baseline)
- `max_iterations` reached (default: 5)

See the `optimize:` section in `config.example.yaml` for all options.

### Deploying to Phoenix

```bash
python pipeline.py deploy --config config.yaml \
  --prompt-file results/optimized_prompt.txt \
  --prompt-name generate_referrals_centraltx \
  --description "Auto-optimized v54"
```

## Configuration

Copy `config.example.yaml` and customize:

```yaml
phoenix:
  url: https://your-phoenix-instance.example.com
  project_name: default
  days_back: 60

extraction:
  adapter: referral    # Use 'referral' for referral systems

evaluation:
  resource_path: resources
  dimensions:
    readability: { enabled: true, max_grade_level: 8.0 }
    url_validity: { enabled: true, skip_validation: false }
    contact_completeness: { enabled: true }
    # ... see config.example.yaml for all options

# Automated optimization (optional)
optimize:
  prompt_name: generate_referrals_centraltx  # Load from Phoenix
  test_corpus_path: test_corpus.json
  max_iterations: 5
  flag_threshold: 2
  auto_deploy: false
```

## Quality Dimensions

These dimensions are designed for referral output quality:

| Dimension | What It Checks | Flags |
|-----------|---------------|-------|
| `output_structure` | Valid JSON with expected keys | `INVALID_JSON`, `ZERO_RESOURCES` |
| `resource_count` | Resource count within bounds | `TOO_FEW_RESOURCES`, `EXCESSIVE_RESOURCES` |
| `url_validity` | HTTP HEAD on resource URLs | `BROKEN_URL`, `HOMEPAGE_ONLY` |
| `readability` | Flesch-Kincaid grade level | `ABOVE_8TH_GRADE` |
| `duplicates` | Fuzzy name/address matching | `DUPLICATE_RESOURCE` |
| `contact_completeness` | Phone/address presence | `MISSING_CONTACT_N` |
| `rag_grounding` | Output vs input context match | `UNGROUNDED_RESOURCE` |
| `location_match` | Geographic consistency | `CROSS_STATE` |

## Adapters

- **`referral`** — For referral/recommendation systems with ReadableLogger + ChatPromptBuilder spans.
- **`generic`** — Basic adapter that works with any system. Finds the longest output span and tries to parse JSON.

See [`docs/adapters.md`](docs/adapters.md) for writing custom adapters.

## Methodology

See [`docs/methodology.md`](docs/methodology.md) for the full methodology writeup including statistical approach, sampling strategy, and prompt engineering insights.

## Relationship to Experiment 12

This experiment (13) is the "outer loop" — the full evaluation and optimization pipeline. Experiment 12 is the "inner loop" — focused specifically on prompt A/B testing. Phase 6 (Iterate) bundles the same prompt testing modules as Experiment 12.

You can use them independently:
- **Experiment 12 alone:** Quick prompt comparison without the full pipeline
- **Experiment 13 alone:** Full evaluation on production data with automated optimization
- **Both together:** Full pipeline with prompt iteration

## Generalizing Beyond Referrals

This pipeline is referral-specific in three places:

1. **`lib/prompt_improver.py`** — The `FIX_STRATEGIES` map and LLM meta-prompt encode referral-specific fix patterns (e.g., "use homepage URL", "every resource MUST have phone/address"). A generic version would need configurable or auto-generated strategies.
2. **`prompt_testing/output_parser.py`** — Top-level JSON arrays are auto-wrapped as `{"resources": [...]}`. Other output schemas would need a different key.
3. **`phases/optimize.py`** — Template variables (`user_query`, `resources_context`, `location`, etc.) are hardcoded to the referral prompt schema.

Everything else (Phoenix client, dimensions framework, statistical analysis, A/B testing, config system) is domain-agnostic. A generalized version that makes these three pieces configurable would be a good candidate for a separate repo.
