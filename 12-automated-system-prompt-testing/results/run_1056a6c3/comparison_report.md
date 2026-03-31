# Web UI A/B Test

**Generated:** 2026-03-27 12:18
**Test queries:** 5
**Model:** gpt-5.1 (temp=0.5)
**Versions:** baseline, variant

## Executive Summary

**baseline vs variant:** baseline wins 1, variant wins 0, tied 4

## Overall Metrics

| Metric | baseline | variant |
|--------|-----|-----|
| Valid JSON | 5/5 | 2/5 |
| Avg resources | 6.6 | 0.0 |
| Avg flags | 1.6 | 2.0 |

## Per-Dimension Comparison

| Dimension | baseline | variant |
|-----------|-----|-----|
| Duplicate resources | 0/5 | 0/5 |
| Avg grade level | 0.0 | 0.0 |
| Above 8th grade | 0/5 | 0/5 |
| Avg grounding % | 60.0% | 0.0% |
| Broken URLs | 0/5 | 0/5 |
| Cross-state errors | 0/5 | 0/5 |
| Missing contact info | 0/5 | 0/5 |

## Flag Distribution

| Flag | baseline | variant |
|------|-----|-----|
| EMPTY_OUTPUT | 0 | 3 |
| HALLUCINATION_RISK | 4 | 0 |
| LOW_GROUNDING | 4 | 0 |
| TOO_FEW_RESOURCES | 0 | 5 |
| ZERO_RESOURCES | 0 | 2 |

## Per-Query Results

| # | Query | baseline Res | baseline Flags | variant Res | variant Flags | Best |
|---|-------|---------|-----------|---------|-----------|------|
| 1 | My client needs food assistance.
Include... | 7 | 2 | 0 | 2 | **tie** |
| 2 | CPR Training
Include resources that supp... | 5 | 0 | 0 | 2 | **baseline** |
| 3 | Include resources that support the follo... | 7 | 2 | 0 | 2 | **tie** |
| 4 | Include resources that support the follo... | 7 | 2 | 0 | 2 | **tie** |
| 5 | My client is a veteran who needs mental ... | 7 | 2 | 0 | 2 | **tie** |

## Regressions (variant worse than baseline)

### q_002
- **Query:** CPR Training
Include resources that support the following categories: Employment
- **baseline flags (0):** none
- **variant flags (2):** EMPTY_OUTPUT, TOO_FEW_RESOURCES
