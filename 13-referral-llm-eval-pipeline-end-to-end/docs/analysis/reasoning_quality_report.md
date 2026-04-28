# Reasoning Quality Test: Does Reasoning Effort Affect Output Quality?

**Generated:** 2026-04-13 20:21  
**Model:** gpt-5.1 | **Temperature:** 0.5 (reasoning="none" only)  
**Prompt:** Production v53 (Goodwill Central Texas Referral)  
**Test corpus:** 20 real production queries from Phoenix (with full RAG context)  
**Conditions:** reasoning="none", "low", "medium", "high"  
**Planned calls:** 80 (20 queries × 4 levels)  
**Completed calls:** 50 (high reasoning caused persistent timeouts/hangs)

## Executive Summary

**Reasoning does not improve output quality — and actively degrades reliability.**

| Level | Avg Flags | Avg Latency | Web Search Rate | Completed |
|-------|-----------|-------------|-----------------|-----------|
| none | **1.71** | **16s** | 65% | 17/20 |
| low | 1.83 | 28s | 83% | 18/20 |
| medium | 2.00 | 96s | 88% | 8/20 |
| high | 2.86 | 252s | 100% | 7/20 |

- **Best quality:** reasoning="none" (1.71 avg flags/query)
- **Worst quality:** reasoning="high" (2.86 avg flags/query — **1.7x more flags**)
- **Speed penalty:** reasoning="high" is **16x slower** than "none"
- **Reliability:** reasoning="high" caused persistent hangs requiring process kills; 13/20 queries never completed

## Quality Flags by Reasoning Level

Lower flags = better quality. Each flag represents a quality issue detected by the automated 7-dimension evaluation.

| Metric | none | low | medium | high |
|--------|------|-----|--------|------|
| Queries completed | 17 | 18 | 8 | 7 |
| Total flags | 29 | 33 | 16 | 20 |
| Avg flags/query | **1.71** | 1.83 | 2.00 | 2.86 |
| Median flags | 2.0 | 2.0 | 2.0 | 3.0 |
| Std dev | 0.69 | 0.71 | 0.76 | 0.69 |
| Min flags | 1 | 1 | 1 | 2 |
| Max flags | 3 | 3 | 3 | 4 |

## Pairwise Win Rates

For each query tested at both levels, which level produced fewer quality flags?

| Matchup | A wins | B wins | Ties | Queries compared |
|---------|--------|--------|------|------------------|
| none vs low | 4 | 2 | 10 | 16 |
| none vs medium | 3 | 0 | 4 | 7 |
| none vs high | 5 | 0 | 2 | 7 |
| low vs medium | 2 | 1 | 4 | 7 |
| low vs high | 5 | 0 | 2 | 7 |
| medium vs high | 1 | 0 | 1 | 2 |

## Speed Comparison

| Level | Mean (s) | Median (s) | Std Dev | Min (s) | Max (s) |
|-------|----------|------------|---------|---------|---------|
| none | 15.9 | 13.7 | 11.3 | 0.8 | 49.8 |
| low | 27.5 | 23.9 | 12.1 | 3.3 | 52.9 |
| medium | 96.3 | 99.5 | 35.1 | 38.2 | 144.2 |
| high | 252.1 | 237.1 | 95.7 | 91.4 | 376.4 |

Latency increases monotonically with reasoning effort: none → low (1.7x) → medium (6.1x) → high (15.9x).

## Web Search Rate by Level

| Level | Web Searches | Rate |
|-------|-------------|------|
| none | 11/17 | 65% |
| low | 15/18 | 83% |
| medium | 7/8 | 88% |
| high | 7/7 | 100% |

Higher reasoning levels trigger web search more frequently — reasoning="high" used web search on 100% of queries vs 65% for "none". This contributes to the latency increase but does not improve quality.

## Reliability Analysis

The most striking finding is not quality or speed — it's **reliability**:

| Level | Completed | Timed out / Hung | Completion rate |
|-------|-----------|------------------|-----------------|
| none | 17/20 | 3 | 85.0% |
| low | 18/20 | 2 | 90.0% |
| medium | 8/20 | 12 | 40.0% |
| high | 7/20 | 13 | 35.0% |

reasoning="high" with production-length prompts (~15K char RAG context) frequently caused the API to hang beyond the 180s timeout, requiring process kills. Multiple attempts across 3 separate runs showed the same pattern: "high" reasoning calls would either complete in 85-376s or hang indefinitely.

This confirms the earlier speed test findings that reasoning="high" had 4 connection errors in 20 queries — but the problem is worse with production-length prompts.

## Conclusion

**Reasoning effort provides zero quality benefit for structured JSON generation tasks.**

The data shows a clear monotonic pattern:

1. **Quality degrades** as reasoning increases: none (1.71 avg flags) → low (1.83) → medium (2.00) → high (2.86)
2. **Latency increases** dramatically: none (16s) → low (28s) → medium (96s) → high (252s)  
3. **Reliability decreases**: reasoning="high" hangs on production prompts, failing to complete 65% of queries
4. **Web search increases** with reasoning (65% → 83% → 88% → 100%), adding latency without quality improvement

The likely explanation: reasoning is designed for complex multi-step logic problems, not structured data retrieval. For our referral tool, the task is "find matching resources and format as JSON" — adding reasoning overhead causes the model to overthink, trigger unnecessary web searches, and produce more verbose (and flag-prone) outputs.

### Recommendation for Blog Post

> **Claim:** "For structured output tasks like resource referrals, OpenAI's reasoning parameter makes responses 2-16x slower, introduces timeout failures, and provides no quality improvement. Our production data shows reasoning='none' produces the best quality at the lowest latency."

This is supported by 50 API calls against 20 real production queries with full RAG context.

### Recommended Production Config

```python
reasoning={"effort": "none"}
temperature=0.5
```

This is the current production configuration and should remain unchanged.
