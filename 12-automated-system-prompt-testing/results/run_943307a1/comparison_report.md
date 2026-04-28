# Web UI A/B Test

**Generated:** 2026-03-27 11:30
**Test queries:** 5
**Model:** gpt-5.1 (temp=0.5)
**Versions:** baseline, variant

## Executive Summary

**baseline vs variant:** baseline wins 1, variant wins 1, tied 3

## Overall Metrics

| Metric | baseline | variant |
|--------|-----|-----|
| Valid JSON | 5/5 | 4/5 |
| Avg resources | 6.4 | 5.0 |
| Avg flags | 1.2 | 1.2 |

## Per-Dimension Comparison

| Dimension | baseline | variant |
|-----------|-----|-----|
| Duplicate resources | 0/5 | 0/5 |
| Avg grade level | 0.0 | 0.0 |
| Above 8th grade | 0/5 | 0/5 |
| Avg grounding % | 57.9% | 58.9% |
| Broken URLs | 0/5 | 0/5 |
| Cross-state errors | 0/5 | 0/5 |
| Missing contact info | 0/5 | 0/5 |

## Flag Distribution

| Flag | baseline | variant |
|------|-----|-----|
| EMPTY_OUTPUT | 0 | 1 |
| HALLUCINATION_RISK | 3 | 2 |
| LOW_GROUNDING | 3 | 2 |
| TOO_FEW_RESOURCES | 0 | 1 |

## Per-Query Results

| # | Query | baseline Res | baseline Flags | variant Res | variant Flags | Best |
|---|-------|---------|-----------|---------|-----------|------|
| 1 | My client needs food assistance.
Include... | 7 | 2 | 7 | 2 | **tie** |
| 2 | CPR Training
Include resources that supp... | 4 | 0 | 4 | 2 | **baseline** |
| 3 | Include resources that support the follo... | 7 | 2 | 7 | 0 | **variant** |
| 4 | Include resources that support the follo... | 7 | 2 | 0 | 2 | **tie** |
| 5 | My client is a veteran who needs mental ... | 7 | 0 | 7 | 0 | **tie** |

## Regressions (variant worse than baseline)

### q_002
- **Query:** CPR Training
Include resources that support the following categories: Employment
- **baseline flags (0):** none
- **variant flags (2):** LOW_GROUNDING, HALLUCINATION_RISK
