# Web UI A/B Test

**Generated:** 2026-03-27 10:19
**Test queries:** 20
**Model:** gpt-5.1 (temp=0.5)
**Versions:** baseline, variant

## Executive Summary

**baseline vs variant:** baseline wins 5, variant wins 1, tied 14

## Overall Metrics

| Metric | baseline | variant |
|--------|-----|-----|
| Valid JSON | 19/20 | 15/20 |
| Avg resources | 6.0 | 4.3 |
| Avg flags | 0.9 | 1.3 |

## Per-Dimension Comparison

| Dimension | baseline | variant |
|-----------|-----|-----|
| Duplicate resources | 0/20 | 0/20 |
| Avg grade level | 0.0 | 0.0 |
| Above 8th grade | 0/20 | 0/20 |
| Avg grounding % | 67.4% | 64.3% |
| Broken URLs | 0/20 | 0/20 |
| Cross-state errors | 0/20 | 0/20 |
| Missing contact info | 0/20 | 0/20 |

## Flag Distribution

| Flag | baseline | variant |
|------|-----|-----|
| EMPTY_OUTPUT | 0 | 5 |
| HALLUCINATION_RISK | 8 | 8 |
| INVALID_JSON | 1 | 0 |
| LOW_GROUNDING | 8 | 8 |
| TOO_FEW_RESOURCES | 1 | 5 |

## Per-Query Results

| # | Query | baseline Res | baseline Flags | variant Res | variant Flags | Best |
|---|-------|---------|-----------|---------|-----------|------|
| 1 | My client needs food assistance.
Include... | 4 | 0 | 5 | 2 | **baseline** |
| 2 | CPR Training
Include resources that supp... | 3 | 0 | 3 | 0 | **tie** |
| 3 | Include resources that support the follo... | 7 | 2 | 0 | 2 | **tie** |
| 4 | Include resources that support the follo... | 7 | 2 | 7 | 2 | **tie** |
| 5 | My client is a veteran who needs mental ... | 7 | 0 | 7 | 2 | **baseline** |
| 6 | My client is a single mom escaping domes... | 7 | 0 | 5 | 2 | **baseline** |
| 7 | My client is a senior citizen who can't ... | 5 | 2 | 0 | 2 | **tie** |
| 8 | Client recently released from incarcerat... | 7 | 2 | 7 | 2 | **tie** |
| 9 | I need help paying my electric bill this... | 0 | 2 | 5 | 2 | **tie** |
| 10 | My client is pregnant and uninsured. She... | 7 | 2 | 5 | 2 | **tie** |
| 11 | Client needs substance abuse treatment. ... | 7 | 0 | 0 | 2 | **baseline** |
| 12 | My client is an immigrant and needs help... | 7 | 0 | 7 | 0 | **tie** |
| 13 | My client is a teenager who ran away fro... | 7 | 0 | 5 | 0 | **tie** |
| 14 | Client has diabetes and can't afford the... | 7 | 2 | 0 | 2 | **tie** |
| 15 | My client is disabled and needs help app... | 7 | 2 | 7 | 0 | **variant** |
| 16 | Client is homeless and needs a place to ... | 5 | 0 | 0 | 2 | **baseline** |
| 17 | My client's child has been diagnosed wit... | 7 | 0 | 7 | 0 | **tie** |
| 18 | I just lost my job and need help with gr... | 6 | 2 | 6 | 2 | **tie** |
| 19 | Client needs dental care but has no insu... | 7 | 0 | 4 | 0 | **tie** |
| 20 | My client is an elderly person living al... | 7 | 0 | 7 | 0 | **tie** |

## Regressions (variant worse than baseline)

### q_001
- **Query:** My client needs food assistance.
Include resources that support the following ca
- **baseline flags (0):** none
- **variant flags (2):** LOW_GROUNDING, HALLUCINATION_RISK

### q_005
- **Query:** My client is a veteran who needs mental health support and employment assistance
- **baseline flags (0):** none
- **variant flags (2):** LOW_GROUNDING, HALLUCINATION_RISK

### q_006
- **Query:** My client is a single mom escaping domestic violence. She needs a safe place to 
- **baseline flags (0):** none
- **variant flags (2):** LOW_GROUNDING, HALLUCINATION_RISK

### q_011
- **Query:** Client needs substance abuse treatment. Prefers outpatient.
Include resources th
- **baseline flags (0):** none
- **variant flags (2):** EMPTY_OUTPUT, TOO_FEW_RESOURCES

### q_016
- **Query:** Client is homeless and needs a place to shower, do laundry, and get mail.
Includ
- **baseline flags (0):** none
- **variant flags (2):** EMPTY_OUTPUT, TOO_FEW_RESOURCES
