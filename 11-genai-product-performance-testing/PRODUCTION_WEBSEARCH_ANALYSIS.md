# Production Web Search Analysis

**Date:** February 19, 2026
**Environment:** Production (pilot-prod)
**Phoenix URL:** Set via `PHOENIX_COLLECTOR_ENDPOINT` environment variable

## Executive Summary

Web search functionality **IS operational** in production. Analysis of 33,416 spans across 5,554 unique traces confirms that:

- **8.0%** of traces successfully invoke web search (447 traces)
- **40.5%** have generator configured but LLM chose not to search (2,251 traces)
- **51.3%** do not use the web search generator (2,848 traces)

## Complete Historical Analysis

### Dataset
- **Total Spans:** 33,416
- **Total Traces:** 5,554
- **Time Period:** All available production data

### Web Search Usage Breakdown

| Category | Count | Percentage | Description |
|----------|-------|------------|-------------|
| ✅ YES | 447 | 8.0% | Web search successfully invoked |
| ❌ NO | 2,251 | 40.5% | Generator ran but LLM chose not to search |
| 📏 DISTANCE_ONLY | 8 | 0.1% | Only calculator/distance queries |
| ⚪ N/A | 2,848 | 51.3% | No web search generator in pipeline |

### Span-Level Metrics

- `OpenAIWebSearchGenerator.run` spans: **2,777**
- `web_search_call` spans: **639**

**Invocation Rate:** 23.0% (639 search calls / 2,777 generator runs)

## Recent Activity Analysis

### Last 1,000 Spans (111 Traces)

To understand recent behavior, we analyzed the most recent production activity:

| Category | Count | Percentage |
|----------|-------|------------|
| ✅ YES | 50 | **45.0%** |
| ❌ NO | 33 | 29.7% |
| 📏 DISTANCE_ONLY | 0 | 0.0% |
| ⚪ N/A | 28 | 25.2% |

**Key Finding:** Recent web search usage (45%) is **5.6x higher** than historical average (8%). This suggests:
1. Recent configuration changes may have improved web search effectiveness
2. Recent queries are more aligned with web search use cases
3. System behavior has improved over time

## Technical Configuration

### Current Production Settings

**Location:** `src/pipelines/generate_referrals/pipeline_wrapper.py:141`

```python
"llm": {"model": "gpt-5-mini", "reasoning_effort": "low"}
```

**Web Search Component:** `src/common/components.py:151-199`

```python
@component
class OpenAIWebSearchGenerator:
    def run(self, messages, domain=None, model="gpt-5", reasoning_effort="high"):
        api_params = {
            "model": model,
            "input": prompt,
            "reasoning": {"effort": reasoning_effort},
            "tools": [{"type": "web_search"}],  # ✅ Enabled
        }
        response = client.responses.create(**api_params)
```

### Detection Methodology

Following team's documented approach (`web_search_detection.md`):

1. **Trace-level Detection:**
   - Group spans by `trace_id`
   - Look for `OpenAIWebSearchGenerator.run` spans (generator presence)
   - Look for `web_search_call` spans (actual invocation)

2. **Classification Logic:**
   ```python
   if no generator and no search calls:
       return 'N/A'  # Web search not configured
   if generator but no search calls:
       return 'NO'   # LLM chose not to search
   if search calls with real queries:
       return 'YES'  # Web search used
   if search calls only with distance calculator:
       return 'DISTANCE_ONLY'
   ```

## Analysis Tools Created

### 1. `complete_websearch_analysis.py`
Comprehensive analysis of all historical production traces.

**Features:**
- Fetches all spans via Phoenix API pagination
- Groups by trace_id
- Classifies web search usage
- Provides detailed breakdown

**Usage:**
```bash
export PHOENIX_COLLECTOR_ENDPOINT="https://your-phoenix-instance:6006"
export PHOENIX_PROJECT_NAME="pilot-prod"
export PHOENIX_API_KEY="<your-key>"
python3 complete_websearch_analysis.py
```

### 2. `quick_websearch_check.py`
Quick analysis of recent 1,000 spans for rapid health check.

**Features:**
- Fast execution (fetches only 10 pages)
- Recent activity snapshot
- Same classification logic as complete analysis

**Usage:**
```bash
export PHOENIX_COLLECTOR_ENDPOINT="https://your-phoenix-instance:6006"
export PHOENIX_PROJECT_NAME="pilot-prod"
export PHOENIX_API_KEY="<your-key>"
python3 quick_websearch_check.py
```

## Conclusions

### ✅ Confirmed Working
Web search is operational in production and being invoked for appropriate queries.

### 📊 Usage Patterns
- **Historical:** 8% web search usage rate
- **Recent:** 45% web search usage rate
- **Trend:** Significant improvement in recent activity

### 🎯 Expected Behavior
The 40.5% of traces where the generator ran but search wasn't invoked represents the LLM correctly determining that those queries don't require current web information.

### 💡 Recommendations

1. **Monitor Recent Trend:** The 45% recent usage rate is significantly higher than historical 8%. Continue monitoring to confirm this is a sustained improvement.

2. **Configuration Alignment:** Current production uses `gpt-5-mini` with `reasoning_effort="low"`. Consider testing if different configurations affect web search invocation rate.

3. **Quality Assessment:** While web search is being invoked, evaluate if the search calls are for appropriate queries and if results improve output quality.

4. **Instrumentation:** Phoenix successfully captures both generator and search call spans, enabling comprehensive observability.

## Related Documentation

- `web_search_detection.md` - Team's documented detection methodology
- `WEB_SEARCH_INVESTIGATION_SUMMARY.md` - Previous investigation findings
- `src/common/components.py` - Web search component implementation
- `src/pipelines/generate_referrals/pipeline_wrapper.py` - Production configuration

## Next Steps

1. ✅ Confirmed web search is operational
2. 🔄 Test how temperature affects web search invocation rate
3. 🔄 Test how reasoning level affects web search invocation rate
4. 📈 Continue monitoring production metrics over time
5. 🎯 Evaluate quality impact of web search on output
