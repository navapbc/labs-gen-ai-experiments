# Evaluation Methodology

This document describes the 6-phase methodology for evaluating LLM output quality at scale.

## Overview

The pipeline answers: **"How good are our LLM outputs, and how can we make them better?"**

It combines automated rule-based checks with statistical analysis to produce actionable improvement recommendations — and then tests those improvements via A/B testing.

## Phase 1: Extract

**Goal:** Pull production traces from your observability system into structured data.

- Connects to Phoenix API (or any trace store) via configurable adapters
- Groups spans by trace ID
- Extracts: prompt type, user query, LLM output, RAG context, metadata
- Outputs: `traces.json` (full data) + `traces.csv` (summary)

**Key design decision:** The adapter pattern allows this pipeline to work with any LLM system. You write a `TraceAdapter` that knows how to find the query, output, and resources in your system's span structure.

## Phase 2: Evaluate

**Goal:** Run automated quality checks on every trace.

Up to 8 configurable dimensions:

| Dimension | What It Checks | Why It Matters |
|-----------|---------------|----------------|
| Output Structure | Valid JSON, expected keys | Basic functionality |
| Resource Count | Within min/max bounds | Completeness |
| URL Validity | HTTP HEAD on URLs | Accuracy |
| Readability | Flesch-Kincaid grade level | Accessibility |
| Duplicates | Fuzzy name/address matching | Quality |
| Contact Completeness | Phone/address presence | Usefulness |
| RAG Grounding | Output vs input context | Hallucination prevention |
| Location Match | Geographic consistency | Relevance |

Each dimension produces binary flags (pass/fail). A trace's total flag count is used as its quality score.

## Phase 3: Sample

**Goal:** Select a representative subset for manual deep review.

- Stratified sampling by prompt type (proportional allocation)
- Oversamples flagged traces (up to 50% of each stratum)
- Configurable target sample size
- Outputs: `sample.json` + markdown review checklist

**Why stratify?** Different prompt types may have different error patterns. Proportional allocation ensures each type is represented in the sample proportionally to its frequency in production.

## Phase 4: Analyze

**Goal:** Statistical analysis with confidence intervals.

- Wilson score confidence intervals for all rates
- Stratified comparison by prompt type, web search usage
- RAG grounding distribution analysis
- Generates markdown evaluation report

**Why Wilson CI?** For proportions (especially near 0 or 1), Wilson intervals are more accurate than normal approximation intervals. They're asymmetric and always stay within [0, 1].

## Phase 5: Improve

**Goal:** Map error patterns to concrete prompt improvements.

- Counts flag occurrences across all traces
- Maps each flag type to known improvement strategies
- Prioritizes by severity (CRITICAL > HIGH > MEDIUM > LOW)
- Outputs prioritized recommendation list

**Key insight from our research:** The most effective prompt improvements are:
1. **Prescriptive word bans** >> abstract readability instructions
2. **Homepage-only URL default** >> "use homepage if unsure"
3. **Named org blocklists** >> generic dedup rules
4. **Structural constraints** ("NEVER empty array") >> behavioral suggestions
5. **Pre-submission checklists** catch errors that instructions miss
6. **Strict grounding** ("MUST only use reference list") >> soft preference

## Phase 6: Iterate

**Goal:** A/B test prompt changes to verify improvements.

- Runs baseline and improved prompts through same test corpus
- Evaluates both versions with same dimensions
- Generates comparison report with:
  - Pairwise wins/losses/ties
  - Per-dimension improvements
  - Regression detection
  - Per-query detail

This phase bundles the same tooling as Experiment 12 (Automated System Prompt A/B Testing).

## Workflow

```
Extract → Evaluate → Sample → Analyze → Improve → Iterate
   ↑                                                  │
   └──────────────── Deploy improved prompt ──────────┘
```

The loop continues until quality targets are met. In our experience, 3-6 prompt iterations are typically needed to achieve significant improvement.

## Adapting for Your System

1. **Write an adapter** — Implement `TraceAdapter` for your span structure (see `docs/adapters.md`)
2. **Configure dimensions** — Enable/disable checks and set thresholds
3. **Set resource_path** — Tell the evaluator where to find resources in your output JSON
4. **Run phases 1-5** on your production data
5. **Apply recommendations** to your prompt
6. **Run phase 6** to verify improvements
