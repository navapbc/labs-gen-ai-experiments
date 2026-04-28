# Web UI A/B Test

**Generated:** 2026-03-27 11:50
**Test queries:** 5
**Model:** gpt-5.1 (temp=0.5)
**Versions:** baseline, variant

## Executive Summary

**baseline vs variant:** baseline wins 1, variant wins 3, tied 1

## Overall Metrics

| Metric | baseline | variant |
|--------|-----|-----|
| Valid JSON | 3/5 | 5/5 |
| Avg resources | 3.4 | 6.0 |
| Avg flags | 2.0 | 1.2 |

## Per-Dimension Comparison

| Dimension | baseline | variant |
|-----------|-----|-----|
| Duplicate resources | 1/5 | 1/5 |
| Avg grade level | 0.0 | 0.0 |
| Above 8th grade | 0/5 | 0/5 |
| Avg grounding % | 31.8% | 50.6% |
| Broken URLs | 0/5 | 0/5 |
| Cross-state errors | 0/5 | 0/5 |
| Missing contact info | 0/5 | 0/5 |

## Flag Distribution

| Flag | baseline | variant |
|------|-----|-----|
| DUPLICATE_RESOURCE | 1 | 1 |
| EMPTY_OUTPUT | 2 | 0 |
| HALLUCINATION_RISK | 2 | 2 |
| LOW_GROUNDING | 3 | 3 |
| TOO_FEW_RESOURCES | 2 | 0 |

## Per-Query Results

| # | Query | baseline Res | baseline Flags | variant Res | variant Flags | Best |
|---|-------|---------|-----------|---------|-----------|------|
| 1 | My client needs food assistance.
Include... | 7 | 2 | 4 | 1 | **variant** |
| 2 | CPR Training
Include resources that supp... | 3 | 1 | 5 | 2 | **baseline** |
| 3 | Include resources that support the follo... | 7 | 3 | 7 | 3 | **tie** |
| 4 | Include resources that support the follo... | 0 | 2 | 7 | 0 | **variant** |
| 5 | My client is a veteran who needs mental ... | 0 | 2 | 7 | 0 | **variant** |

## Regressions (variant worse than baseline)

### q_002
- **Query:** CPR Training
Include resources that support the following categories: Employment
- **baseline flags (1):** LOW_GROUNDING
- **variant flags (2):** LOW_GROUNDING, HALLUCINATION_RISK
