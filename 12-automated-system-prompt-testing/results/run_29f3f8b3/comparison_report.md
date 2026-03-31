# Web UI A/B Test

**Generated:** 2026-03-27 15:49
**Test queries:** 20
**Model:** gpt-5.1 (temp=0.5)
**Versions:** baseline, variant

## Executive Summary

**baseline vs variant:** baseline wins 10, variant wins 1, tied 9

## Overall Metrics

| Metric | baseline | variant |
|--------|-----|-----|
| Valid JSON | 20/20 | 6/20 |
| Avg resources | 6.2 | 0.8 |
| Avg flags | 1.1 | 1.9 |

## Per-Dimension Comparison

| Dimension | baseline | variant |
|-----------|-----|-----|
| Duplicate resources | 0/20 | 0/20 |
| Avg grade level | 0.0 | 0.0 |
| Above 8th grade | 0/20 | 0/20 |
| Avg grounding % | 61.2% | 65.7% |
| Broken URLs | 1/20 | 0/20 |
| Cross-state errors | 0/20 | 0/20 |
| Missing contact info | 0/20 | 0/20 |

## Flag Distribution

| Flag | baseline | variant |
|------|-----|-----|
| BROKEN_URL | 1 | 0 |
| EMPTY_OUTPUT | 0 | 14 |
| HALLUCINATION_RISK | 10 | 2 |
| LOW_GROUNDING | 10 | 2 |
| TOO_FEW_RESOURCES | 0 | 17 |
| ZERO_RESOURCES | 0 | 3 |

## Per-Query Results

| # | Query | baseline Res | baseline Flags | variant Res | variant Flags | Best |
|---|-------|---------|-----------|---------|-----------|------|
| 1 | My client needs food assistance.
Include... | 7 | 2 | 0 | 2 | **tie** |
| 2 | CPR Training
Include resources that supp... | 5 | 0 | 0 | 2 | **baseline** |
| 3 | Include resources that support the follo... | 7 | 2 | 0 | 2 | **tie** |
| 4 | Include resources that support the follo... | 7 | 2 | 0 | 2 | **tie** |
| 5 | My client is a veteran who needs mental ... | 7 | 0 | 0 | 2 | **baseline** |
| 6 | My client is a single mom escaping domes... | 7 | 2 | 5 | 0 | **variant** |
| 7 | My client is a senior citizen who can't ... | 5 | 0 | 0 | 2 | **baseline** |
| 8 | Client recently released from incarcerat... | 7 | 2 | 0 | 2 | **tie** |
| 9 | I need help paying my electric bill this... | 7 | 2 | 0 | 2 | **tie** |
| 10 | My client is pregnant and uninsured. She... | 7 | 2 | 5 | 2 | **tie** |
| 11 | Client needs substance abuse treatment. ... | 6 | 2 | 0 | 2 | **tie** |
| 12 | My client is an immigrant and needs help... | 7 | 0 | 7 | 2 | **baseline** |
| 13 | My client is a teenager who ran away fro... | 5 | 0 | 0 | 2 | **baseline** |
| 14 | Client has diabetes and can't afford the... | 7 | 2 | 0 | 2 | **tie** |
| 15 | My client is disabled and needs help app... | 7 | 0 | 0 | 2 | **baseline** |
| 16 | Client is homeless and needs a place to ... | 4 | 1 | 0 | 2 | **baseline** |
| 17 | My client's child has been diagnosed wit... | 5 | 0 | 0 | 2 | **baseline** |
| 18 | I just lost my job and need help with gr... | 6 | 2 | 0 | 2 | **tie** |
| 19 | Client needs dental care but has no insu... | 4 | 0 | 0 | 2 | **baseline** |
| 20 | My client is an elderly person living al... | 7 | 0 | 0 | 2 | **baseline** |

## Regressions (variant worse than baseline)

### q_002
- **Query:** CPR Training
Include resources that support the following categories: Employment
- **baseline flags (0):** none
- **variant flags (2):** EMPTY_OUTPUT, TOO_FEW_RESOURCES

### q_005
- **Query:** My client is a veteran who needs mental health support and employment assistance
- **baseline flags (0):** none
- **variant flags (2):** ZERO_RESOURCES, TOO_FEW_RESOURCES

### q_007
- **Query:** My client is a senior citizen who can't drive and needs help getting to doctor a
- **baseline flags (0):** none
- **variant flags (2):** ZERO_RESOURCES, TOO_FEW_RESOURCES

### q_012
- **Query:** My client is an immigrant and needs help understanding their rights. They also n
- **baseline flags (0):** none
- **variant flags (2):** LOW_GROUNDING, HALLUCINATION_RISK

### q_013
- **Query:** My client is a teenager who ran away from home. They need a safe place and someo
- **baseline flags (0):** none
- **variant flags (2):** EMPTY_OUTPUT, TOO_FEW_RESOURCES

### q_015
- **Query:** My client is disabled and needs help applying for SSI and finding accessible hou
- **baseline flags (0):** none
- **variant flags (2):** EMPTY_OUTPUT, TOO_FEW_RESOURCES

### q_016
- **Query:** Client is homeless and needs a place to shower, do laundry, and get mail.
Includ
- **baseline flags (1):** BROKEN_URL
- **variant flags (2):** EMPTY_OUTPUT, TOO_FEW_RESOURCES

### q_017
- **Query:** My client's child has been diagnosed with autism. They need therapy services and
- **baseline flags (0):** none
- **variant flags (2):** EMPTY_OUTPUT, TOO_FEW_RESOURCES

### q_019
- **Query:** Client needs dental care but has no insurance and very limited income.
Include r
- **baseline flags (0):** none
- **variant flags (2):** EMPTY_OUTPUT, TOO_FEW_RESOURCES

### q_020
- **Query:** My client is an elderly person living alone who has been the victim of financial
- **baseline flags (0):** none
- **variant flags (2):** EMPTY_OUTPUT, TOO_FEW_RESOURCES
