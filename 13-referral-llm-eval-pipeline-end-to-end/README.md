# Experiment 13: Referral LLM Evaluation & Optimization Pipeline

A pipeline for evaluating and optimizing LLM-generated resource referrals. Given access to a Phoenix observability instance (or trace data), it extracts traces, runs automated quality checks across 8 dimensions, performs statistical analysis, generates improvement recommendations, and can automatically iterate on prompts until quality targets are met.

> ## 📖 Case study website
>
> For a scrollable, presentation-friendly walkthrough of the evaluation pipeline, open the live website:
> [gobrando.github.io/labs-gen-ai-experiments](https://gobrando.github.io/labs-gen-ai-experiments/)
>
> Repo copy: [docs/case-study/index.html](docs/case-study/index.html)

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

## Standalone Study: Reasoning Effort vs. Output Quality

`reasoning_quality_test.py` is a one-off experiment that reuses the 7 output-quality dimensions from this pipeline to answer a single question: **does raising OpenAI's `reasoning.effort` parameter improve output quality, or just slow things down?**

An earlier speed test (see experiment 11) showed that higher reasoning levels were 2–14x slower and introduced connection errors. That test did not measure quality. This experiment does.

**Design**

- 20 real production queries (extracted from Phoenix, full RAG context preserved)
- 4 reasoning levels: `none`, `low`, `medium`, `high`
- gpt-5.1, temperature=0.5 (fixed for `none`; omitted for the others, which the API requires)
- Production prompt v53
- Randomized test order, per-call hard timeout, checkpoint every 10 calls
- Each output evaluated across the 7 dimensions (`output_structure`, `resource_count`, `url_validity`, `duplicates`, `readability`, `contact_completeness`, `rag_grounding`)

Planned 80 calls; completed 50 across 3 runs after repeated API hangs on `reasoning="high"` (see reliability finding below).

**Findings**

| Level   | Avg flags / query | Avg latency | Web search rate | Completion rate |
|---------|------------------:|------------:|----------------:|----------------:|
| none    | **1.71** | **16s**  | 65%  | 85% |
| low     | 1.83     | 28s      | 83%  | 90% |
| medium  | 2.00     | 96s      | 88%  | 40% |
| high    | 2.86     | 252s     | 100% | 35% |

Three findings, all monotonic in reasoning level:

1. **Quality degrades.** Average flags rise from 1.71 (none) to 2.86 (high). In pairwise matchups, `none` won or tied every comparison — it never lost once.
2. **Latency explodes.** 16s → 252s, a ~16x slowdown for `high`. Web search rate climbs 65% → 100%, which explains some (but not all) of the latency increase.
3. **Reliability collapses.** `medium` and `high` hung past the 180s timeout on more than half of queries with production-length prompts (~15k char RAG context), requiring process kills across three separate runs.

**Bottom line:** For structured JSON resource-referral tasks, raising `reasoning.effort` is strictly worse on all three axes we care about. The current production config (`reasoning="none"`, `temperature=0.5`) is already optimal and should not change.

**Outputs**

- `reasoning_quality_test.py` — the experiment script
- `data/production_test_corpus.json` — the 20-query test corpus with full RAG context
- `data/reasoning_quality_test_results.json` — aggregated per-call results and per-level statistics
- `docs/analysis/reasoning_quality_report.md` — full writeup with pairwise win rates, per-dimension breakdown, and reliability analysis

Run it yourself (costs ~$3–5 in OpenAI API calls):

```bash
export OPENAI_API_KEY=sk-...
python reasoning_quality_test.py
```

Dry-run the pipeline wiring without making API calls:

```bash
python reasoning_quality_test.py --dry-run --sample
```

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
