# GenAI Product Performance Testing Experiments

## Overview

This directory contains comprehensive performance testing and analysis experiments for the Goodwill Central Texas Referral GenAI product. These experiments were conducted to optimize model selection, parameter configuration, and understand web search behavior in the OpenAI Responses API.

## Key Findings Summary

### 1. Model Selection (Phase 1)
- **Winner: Gemini 3 Flash** - 2.15x faster than ChatGPT 5.1
- ChatGPT 5.1: 29.72s avg, 100% success rate, high variability (σ=7.73s)
- Gemini 3 Flash: 13.80s avg, 98.2% success rate, very consistent (σ=1.23s)
- At scale (1,000 requests): Gemini saves 4.4 hours

### 2. Parameter Effect Testing (Phase 2)
**Temperature (0.0-2.0):**
- Web search rate: Stable ~90% across all values
- Minimal effect on behavior
- Temperature 2.0 showed instability (hung queries)

**Reasoning (low, medium, high):**
- Web search rate: 90% → 90% → 95% → 100% (increases with reasoning level)
- Latency: ~20s → ~40s → ~140s → ~280s (dramatically slower)
- Higher reasoning = MORE web search + MUCH slower responses
- Reasoning high had reliability issues (4 connection errors)

**Production Recommendation:**
Keep gpt-5.1 with reasoning="none" for optimal performance:
- Fastest response times (~20s median)
- Most reliable (no hung queries)
- Lowest cost (no reasoning overhead)
- Stable web search behavior

### 3. Web Search Behavior Analysis
**Production Baseline:**
- Real production: 36.4% web search rate (with full database resources)
- Test environment: 90-100% web search rate (CAT/Excel resources only)
- 60pp gap due to missing ~hundreds of database-injected resources

**Root Cause:**
- Database resources are injected into system prompt at runtime
- Test scripts use static prompt with only CAT/Excel resources
- Model correctly uses web search when database resources unavailable

## File Structure

### Documentation Files
- `LATENCY_BENCHMARK_RESULTS.md` - **Primary documentation** with all benchmark results
- `TEMPERATURE_ANALYSIS_REPORT.md` - Detailed temperature parameter analysis
- `WEB_SEARCH_INVESTIGATION_SUMMARY.md` - Investigation into web search spike
- `PRODUCTION_WEBSEARCH_ANALYSIS.md` - Production vs test environment analysis
- `WEB_SEARCH_SPIKE_ROOT_CAUSE_ANALYSIS.md` - Root cause analysis document
- `README.md` - This file

### Test Scripts

**Model Comparison:**
- `comprehensive_50_prompt_benchmark.py` - Main 50-prompt model comparison
- `raw_model_benchmark.py` - Initial 10-prompt comparison
- `phase2_web_search_benchmark.py` - Web search capability testing

**Parameter Testing:**
- `parameter_effect_test.py` - **Main comprehensive parameter testing**
- `temperature_test.py` - Temperature parameter testing
- `reasoning_level_comparison.py` - Reasoning level comparison
- `reasoning_latency_test.py` - Reasoning latency analysis

**Web Search Investigation:**
- `definitive_websearch_detection.py` - Definitive web search detection method
- `production_baseline_test.py` - Production baseline establishment
- `controlled_web_search_test.py` - Controlled testing environment
- `analyze_web_search_reasons.py` - Analysis of why web search is triggered

**Production Analysis:**
- `extract_resources_from_traces_v3.py` - Extract resources from Phoenix traces
- `analyze_phoenix_spans.py` - Phoenix span analysis
- `analyze_traces.py` - Trace analysis utilities

### Results Files

**Key Results:**
- `parameter_effect_results.json` - **Comprehensive parameter test results**
- `sample_production_queries.json` - 55 real production queries used in testing
- `production_prompt_v48.txt` - Production prompt template (v48)

### Test Output Files (test_outputs/)

**Detailed Test Results:** The `test_outputs/` directory contains raw console output from key test runs that provide valuable insights into model behavior:

- `reasoning_comparison_no_temp_output.txt` - **Detailed reasoning level comparison** (37K) showing response times, web search usage, and resource counts across reasoning levels
- `temperature_websearch_analysis_output.txt` - Temperature parameter impact on web search behavior (27K)
- `temperature_test_results.txt` - Temperature parameter testing across multiple values (15K)
- `gpt51_temperature_none_verification.txt` - GPT-5.1 temperature verification test results (8.5K)
- `gpt52_temperature_verification.txt` - GPT-5.2 temperature verification test results (8.2K)
- `production_temperature_results_gpt51.txt` - Production-scale temperature testing with GPT-5.1 (3.5K)
- `production_temperature_results.txt` - Production-scale temperature testing baseline (3.4K)

These files show actual test execution with SUCCESS/ERROR indicators, response times, web search detection, and detailed resource findings. They complement the summarized results in the JSON files and provide the raw data that informed the key findings.

### Supporting Files
- `extracted_production_resources.txt` - Resources extracted from production traces
- `phoenix_prompts_raw.txt` - Raw Phoenix trace data
- Various analysis and intermediate result files

## Methodology

### Testing Approach
1. **Real Production Queries:** Used 55 actual production queries from live system
2. **Controlled Environment:** Isolated variables (model, temperature, reasoning)
3. **Statistical Rigor:** Used median latency to handle outliers, tracked error rates
4. **Baseline Establishment:** Measured production behavior first for comparison

### OpenAI Responses API
- API: `client.responses.create()`
- Web search detection: `response.output` items with `type='web_search_call'`
- Model: gpt-5.1
- Parameters tested: temperature (0.0-2.0), reasoning (none, low, medium, high)

### Production Context
- Phoenix tracing: Production observability via Phoenix (configure via PHOENIX_COLLECTOR_ENDPOINT)
- Database resources: ~Hundreds of resources injected at runtime (not in static prompt)
- System prompt: Jinja2 template with runtime variable injection

## Production Recommendations

### Immediate Actions
1. **Keep current configuration:** gpt-5.1 with reasoning="none"
2. **Don't use higher reasoning levels:** Dramatically slower with minimal benefit
3. **Temperature parameter:** Not significant for this use case, keep at default

### Future Considerations
1. **Model comparison with web search:** Test Gemini with web search capability
2. **Database resource optimization:** Analyze which injected resources are most valuable
3. **Prompt engineering:** Further optimize prompt to reduce unnecessary web searches

## Relationship to Decision Records

These experiments support the following decision records that should be included in the main product repo:

### Decision Record: Model Selection and Configuration

**Context:** Need to optimize API response times and cost while maintaining quality

**Decision:** Use gpt-5.1 with reasoning="none" for production

**Consequences:**
- Fastest median response time (~20s)
- Most cost-effective configuration
- Stable and reliable behavior
- Future opportunity to test Gemini 3 Flash if web search support is added

**Alternatives Considered:**
- Higher reasoning levels: 2-14x slower, unreliable, minimal benefit
- Temperature variations: No significant impact on behavior
- Gemini 3 Flash: 2x faster but lacks web search capability needed for production

## Test Environment

- **Python:** 3.x
- **Dependencies:** openai, httpx, json, time
- **APIs:** OpenAI Responses API, Phoenix tracing API
- **Date Range:** 2026-03-03 (testing period)

## Contact

For questions about these experiments, refer to PR #196 in the main product repo or contact the product team.

---

**Note:** This directory contains experimental code and analysis. The production implementation may differ from test scripts shown here. Always refer to the main product repo for current production code.
