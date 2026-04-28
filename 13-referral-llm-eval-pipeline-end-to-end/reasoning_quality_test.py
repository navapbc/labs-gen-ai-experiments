#!/usr/bin/env python3
"""
Reasoning Quality Test: Does OpenAI reasoning effort affect OUTPUT QUALITY?

Tests 4 reasoning levels (none, low, medium, high) on 20 queries using gpt-5.1
with the production prompt (v53), then runs the 7-dimension automated quality
check on all 80 outputs.

Prior finding: reasoning made responses 2-14x SLOWER and introduced connection
errors — but quality was never measured. This script fills that gap.

Usage:
    export OPENAI_API_KEY=sk-...
    python reasoning_quality_test.py [--skip-url-check] [--dry-run]
"""
import os
import sys
import json
import time
import random
import signal
import argparse
import statistics
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from openai import OpenAI

# Add project root to path for dimension imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from dimensions.output_structure import OutputStructureDimension
from dimensions.resource_count import ResourceCountDimension
from dimensions.url_validity import UrlValidityDimension
from dimensions.duplicates import DuplicatesDimension
from dimensions.readability import ReadabilityDimension
from dimensions.contact_completeness import ContactCompletenessDimension
from dimensions.rag_grounding import RagGroundingDimension
from prompt_testing.output_parser import parse_json, extract_resources

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL = "gpt-5.1"
TEMPERATURE = 0.5
REASONING_LEVELS = ["none", "low", "medium", "high"]
TIMEOUT_SECONDS = 180
MAX_RETRIES = 1
RATE_LIMIT_DELAY = 0.5  # seconds between API calls

# Production prompt v53 (same as parameter_effect_test.py / current production)
PRODUCTION_PROMPT = """You are an API endpoint for Goodwill Central Texas Referral and you return only a JSON object.
You are designed to help career case managers provide high-quality, local resource referrals to client's in Central Texas.
Your role is to support case managers working with low-income job seekers and learners in Austin and surrounding counties (Bastrop, Blanco, Burnet, Caldwell, DeWitt, Fayette, Gillespie, Gonzales, Hays, Lavaca, Lee, Llano, Mason, Travis, Williamson).

## Task Checklist
- Evaluate the client's needs and consider their eligibility for each resource, such as the client's age, income, disability, immigration/veteran status, and number of dependents.
- Suggest recommended resources and rank by proximity and eligibility.
- Never invent or fabricate resources. If none are available, state this clearly. Use trusted sources such as Goodwill, government, vetted nonprofits, and trusted news outlets (Findhelp, 211, Connect ATX permitted). Never use unreliable websites (e.g., shelterlistings.org, needhelppayingbills.com, thehelplist.com). Prefer direct sources rather than websites that aggregate listings.
- NEVER invent or guess URLs. Use only verified URLs that will actually work.
- NEVER offer Texas Workforce Commission OR Capital IDEA unless there's a more specific resource that these services specifically offer that GoodWill does not offer.
- NEVER recommend a resource that is no longer available (e.g., a course with a start date in the past) OR a resource that is unlikely to be available soon (e.g., a site opening in 2027.)

## Response Constraints
- Your response should ONLY include resources from the list below or resources you find searching the web.
- If no resources are found, return only an empty JSON list without any extra text.
- Do not summarize your assessment of the clients needs.
- Limit the description for a resource to be less than 255 words.
- Set referral_type to: "goodwill" if the resource offered by Goodwill (such as the Goodwill Career and Training Academy), "government" for resources provided by the city, county, or state, and "external" for all others.

## Resources
In addition to what you find searching the web, choose from following list of resources:

Career Advancement Training (CAT)
Free short-term training courses (1-4 weeks) covering essential workplace skills and prerequisites. CAT serves as both standalone skill-building and as required preparation for GCTA programs.

\u26a0\ufe0f CRITICAL DISTINCTION: CAT \u2260 GCTA CAT trainings are NOT the same as GCTA trainings. Key differences:
 - Duration: CAT classes are much shorter (1-4 weeks) vs GCTA programs (4-12 weeks)
 - Enrollment: CAT has a simpler, faster enrollment process - often just requires online registration through Wufoo forms
 - Prerequisites: CAT courses often serve as prerequisites TO GCTA programs (e.g., Career Advancement Essentials must be completed before GCTA enrollment)
 - Certification: GCTA leads to industry certifications and job placement; CAT builds foundational skills
 - Complexity: GCTA requires extensive documentation, assessments (Wonderlic/CASAS), and multi-level approvals; CAT enrollment is streamlined

CAT Class Registration Links by Location:

Goodwill Resource Center (GRC/South):
 - Career Advancement Essentials: https://gwcareeradvancement.wufoo.com/forms/grc-career-advancement-essentials/
 - Computer Basics/Keyboarding: https://gwcareeradvancement.wufoo.com/forms/grc-computer-basics/
 - Digital Skills 1:1: https://gwcareeradvancement.wufoo.com/forms/grc-digital-skills-11/
 - Financial Empowerment Training: https://gwcareeradvancement.wufoo.com/forms/grc-11-financial-empowerment-trainings/
 - Indeed Lab: https://gwcareeradvancement.wufoo.com/forms/grc-indeed-lab/
 - Interview Preparation & Practice: https://gwcareeradvancement.wufoo.com/forms/grc-interview-preparation-and-practice/
 - Job Preparation 1:1: https://gwcareeradvancement.wufoo.com/forms/grc-job-preparation-11/
 - Online Safety: https://gwcareeradvancement.wufoo.com/forms/grc-online-safety/
 - Virtual Career Advancement Essentials: https://gwcareeradvancement.wufoo.com/forms/virtual-career-advancement-essentials/

Goodwill Community Center (GCC/North):
 - Career Advancement Essentials: https://gwcareeradvancement.wufoo.com/forms/gcc-career-advancement-essentials/
 - Computer Basics/Keyboarding: https://gwcareeradvancement.wufoo.com/forms/gcc-computer-basics/
 - Digital Skills 1:1: https://gwcareeradvancement.wufoo.com/forms/gcc-digital-skills-11/
 - Financial Empowerment Training: https://gwcareeradvancement.wufoo.com/forms/gcc-11-financial-empowerment-trainings/
 - Indeed Lab: https://gwcareeradvancement.wufoo.com/forms/gcc-indeed-lab/
 - Interview Preparation & Practice: https://gwcareeradvancement.wufoo.com/forms/gcc-interview-preparation-and-practice/
 - Job Preparation 1:1: https://gwcareeradvancement.wufoo.com/forms/gcc-job-preparation-11/
 - Wonderlic Prep & Practice: https://gwcareeradvancement.wufoo.com/forms/gcc-wonderlic-prep-and-practice/
 - AI Basics: https://gwcareeradvancement.wufoo.com/forms/zjgi3bu0u7t757/
 - Online Safety: https://gwcareeradvancement.wufoo.com/forms/zs43hn608egpxa/
 - Virtual Career Advancement Essentials: https://gwcareeradvancement.wufoo.com/forms/virtual-career-advancement-essentials/

When recommending CAT classes:
 - Direct clients to the appropriate location-specific registration link
 - GRC serves South Austin and surrounding areas
 - GCC serves North Austin, Round Rock, Georgetown, and surrounding areas
 - Most classes require pre-registration through the Wufoo forms
 - Classes run on monthly schedules - check with Career Case Manager for current availability

Excel Center High School
Goodwill's tuition-free high school completion program for adults ages 18-50:
- Earn accredited high school diploma (not GED)
- Flexible schedules designed for working adults
- Free childcare during classes
- Career coaching integrated into curriculum
- College prep included
- Small class sizes (15-20 students)
- Usually 12-18 months to complete
- Website: https://excelcenterhighschool.org/
When to recommend: Clients without high school diploma asking about GED should be informed about Excel Center as a superior alternative to traditional GED programs."""


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------
def call_reasoning_api(client: OpenAI, query: str, reasoning_level: str,
                       resources_context: str = "") -> dict:
    """Call OpenAI Responses API with a specific reasoning level.

    Returns dict with: content, response_time, web_search_used, error, usage.
    """
    # Build user message with context if available
    user_content = f"Client needs: {query}"
    if resources_context:
        user_content = (
            f"Client needs: {query}\n\n"
            f"## Available Resources from Database\n{resources_context}"
        )

    request_params = {
        "model": MODEL,
        "tools": [{"type": "web_search"}],
        "input": [
            {"role": "system", "content": PRODUCTION_PROMPT},
            {"role": "user", "content": user_content},
        ],
    }

    # Set reasoning and temperature
    if reasoning_level == "none":
        request_params["reasoning"] = {"effort": "none"}
        request_params["temperature"] = TEMPERATURE
    else:
        # Temperature not compatible with reasoning > none
        request_params["reasoning"] = {"effort": reasoning_level}

    start = time.time()
    try:
        response = client.responses.create(**request_params)
        elapsed = time.time() - start

        # Extract text content and check for web search
        content = ""
        web_search_used = False
        if response.output:
            for item in response.output:
                if hasattr(item, 'type'):
                    if item.type == 'web_search_call':
                        web_search_used = True
                    elif item.type == 'message':
                        for block in getattr(item, 'content', []):
                            if hasattr(block, 'text'):
                                content += block.text

        usage = {}
        if hasattr(response, 'usage') and response.usage:
            usage = {
                'input_tokens': getattr(response.usage, 'input_tokens', 0),
                'output_tokens': getattr(response.usage, 'output_tokens', 0),
                'total_tokens': getattr(response.usage, 'total_tokens', 0),
            }

        return {
            'content': content,
            'response_time': round(elapsed, 2),
            'web_search_used': web_search_used,
            'error': None,
            'usage': usage,
        }

    except Exception as e:
        elapsed = time.time() - start
        return {
            'content': '',
            'response_time': round(elapsed, 2),
            'web_search_used': False,
            'error': str(e)[:200],
            'usage': {},
        }


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate_response(content: str, resources_context: str, location: str,
                      user_query: str, skip_url_check: bool = False) -> dict:
    """Run the 7-dimension quality check on a single response.

    Returns dict with: parsed_json, resources, resource_count, flags, flag_count, details.
    """
    parsed, parse_error = parse_json(content)
    resources = extract_resources(parsed)

    context = {
        'parsed_json': parsed,
        'parse_error': parse_error,
        'raw_content': content,
        'resources_context': resources_context,
        'location': location,
        'user_query': user_query,
    }

    # Initialize dimensions
    dims = [
        OutputStructureDimension(),
        ResourceCountDimension({'min': 1, 'max': 10}),
        UrlValidityDimension({'skip_validation': skip_url_check, 'timeout': 10}),
        DuplicatesDimension(),
        ReadabilityDimension(),
        ContactCompletenessDimension(),
        RagGroundingDimension(),
    ]

    all_flags = []
    details = {}

    for dim in dims:
        result = dim.evaluate(resources, context)
        all_flags.extend(result.flags)
        details[dim.name] = result.details

    return {
        'parsed_json': parsed,
        'resources': resources,
        'resource_count': len(resources),
        'flags': all_flags,
        'flag_count': len(all_flags),
        'details': details,
    }


# ---------------------------------------------------------------------------
# Load test corpus
# ---------------------------------------------------------------------------
def load_test_corpus(use_production: bool = False) -> list[dict]:
    """Load the 20-query test corpus.

    Args:
        use_production: If True, load from data/production_test_corpus.json
            (real queries from Phoenix). Otherwise use sample_data/traces.json.
    """
    if use_production:
        corpus_path = PROJECT_ROOT / 'data' / 'production_test_corpus.json'
        if not corpus_path.exists():
            print(f"ERROR: Production corpus not found at {corpus_path}")
            print("Run the Phoenix extraction script first, or use --sample.")
            sys.exit(1)
        with open(corpus_path) as f:
            traces = json.load(f)
        corpus = []
        for t in traces:
            corpus.append({
                'trace_id': t['trace_id'],
                'user_query': t['user_query'],
                'location': t.get('location', ''),
                'resources_context': t.get('resources_context', ''),
                'prompt_type': t.get('prompt_type', ''),
            })
        print(f"Loaded {len(corpus)} PRODUCTION queries from {corpus_path}")
    else:
        traces_path = PROJECT_ROOT / 'sample_data' / 'traces.json'
        with open(traces_path) as f:
            traces = json.load(f)
        corpus = []
        for t in traces:
            corpus.append({
                'trace_id': t['trace_id'],
                'user_query': t['user_query'],
                'location': t.get('location', ''),
                'resources_context': t.get('resources_context', ''),
                'prompt_type': t.get('prompt_type', ''),
            })
        print(f"Loaded {len(corpus)} sample queries from {traces_path}")

    return corpus


# ---------------------------------------------------------------------------
# Run experiment
# ---------------------------------------------------------------------------
def run_experiment(corpus: list[dict], skip_url_check: bool = False,
                   dry_run: bool = False) -> dict:
    """Run all 80 API calls (20 queries x 4 levels) in randomized order."""
    client = None if dry_run else OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        timeout=TIMEOUT_SECONDS,
    )

    # Build work items: (query_index, reasoning_level)
    work_items = []
    for qi in range(len(corpus)):
        for level in REASONING_LEVELS:
            work_items.append((qi, level))

    # Randomize to avoid systematic bias (e.g., rate limits hitting one level)
    random.shuffle(work_items)

    total = len(work_items)
    print(f"\nRunning {total} API calls ({len(corpus)} queries x "
          f"{len(REASONING_LEVELS)} reasoning levels)")
    print(f"Model: {MODEL} | Temperature: {TEMPERATURE} | "
          f"Timeout: {TIMEOUT_SECONDS}s")
    print(f"Order: randomized | URL checks: {'skipped' if skip_url_check else 'enabled'}")
    print("=" * 80)

    # Store results indexed by (trace_id, reasoning_level)
    results = {}

    for i, (qi, level) in enumerate(work_items, 1):
        query = corpus[qi]
        trace_id = query['trace_id']
        key = (trace_id, level)

        query_short = query['user_query'][:50].replace('\n', ' ')
        print(f"  [{i:3d}/{total}] {level:6s} | {trace_id} | {query_short}...", end="")

        if dry_run:
            # Simulate for testing
            results[key] = {
                'trace_id': trace_id,
                'reasoning_level': level,
                'api_response': {'content': '[]', 'response_time': 0.1,
                                 'web_search_used': False, 'error': None, 'usage': {}},
                'eval': evaluate_response('[]', query['resources_context'],
                                          query['location'], query['user_query'],
                                          skip_url_check),
            }
            print(f" | DRY RUN")
            continue

        # Call API with retry
        api_result = call_reasoning_api(
            client, query['user_query'], level, query['resources_context']
        )

        # Retry once on error
        if api_result['error'] and MAX_RETRIES > 0:
            print(f" | RETRY...", end="")
            time.sleep(2)
            api_result = call_reasoning_api(
                client, query['user_query'], level, query['resources_context']
            )

        # Evaluate
        if api_result['error']:
            eval_result = {
                'parsed_json': None,
                'resources': [],
                'resource_count': 0,
                'flags': ['API_ERROR'],
                'flag_count': 1,
                'details': {'error': api_result['error']},
            }
        else:
            eval_result = evaluate_response(
                api_result['content'],
                query['resources_context'],
                query['location'],
                query['user_query'],
                skip_url_check,
            )

        results[key] = {
            'trace_id': trace_id,
            'reasoning_level': level,
            'api_response': {
                'content': api_result['content'][:5000],  # Truncate for storage
                'response_time': api_result['response_time'],
                'web_search_used': api_result['web_search_used'],
                'error': api_result['error'],
                'usage': api_result['usage'],
            },
            'eval': eval_result,
        }

        status = "ERR" if api_result['error'] else "OK "
        web = "WEB" if api_result['web_search_used'] else "   "
        flags = eval_result['flag_count']
        rt = api_result['response_time']
        print(f" | {status} {web} | {rt:6.1f}s | flags={flags}")

        time.sleep(RATE_LIMIT_DELAY)

        # Checkpoint: save partial results every 10 calls
        if i % 10 == 0:
            checkpoint_path = PROJECT_ROOT / 'data' / 'reasoning_checkpoint.json'
            checkpoint = {str(k): v for k, v in results.items()}
            with open(checkpoint_path, 'w') as f:
                json.dump(checkpoint, f, default=str)

    return results


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
def analyze_results(results: dict, corpus: list[dict]) -> dict:
    """Compute aggregate statistics across reasoning levels."""
    analysis = {}

    for level in REASONING_LEVELS:
        level_results = [v for k, v in results.items() if k[1] == level]

        flag_counts = [r['eval']['flag_count'] for r in level_results]
        response_times = [r['api_response']['response_time'] for r in level_results]
        resource_counts = [r['eval']['resource_count'] for r in level_results]
        error_count = sum(1 for r in level_results if r['api_response']['error'])
        web_search_count = sum(1 for r in level_results
                               if r['api_response']['web_search_used'])

        # Per-dimension flag counts
        dim_flags = defaultdict(int)
        for r in level_results:
            for flag in r['eval']['flags']:
                dim_flags[flag] += 1

        # Grounding percentages
        grounding_pcts = []
        for r in level_results:
            rag = r['eval']['details'].get('rag_grounding', {})
            if rag.get('total', 0) > 0:
                grounding_pcts.append(rag.get('grounding_pct', 0))

        # Readability grades
        readability_grades = []
        for r in level_results:
            read = r['eval']['details'].get('readability', {})
            if isinstance(read, dict):
                rd = read.get('readability', read)
                gl = rd.get('grade_level') or rd.get('flesch_grade')
                if gl is not None:
                    try:
                        readability_grades.append(float(gl))
                    except (ValueError, TypeError):
                        pass

        n = len(level_results)
        analysis[level] = {
            'total_queries': n,
            'total_flags': sum(flag_counts),
            'avg_flags': round(statistics.mean(flag_counts), 2) if flag_counts else 0,
            'median_flags': statistics.median(flag_counts) if flag_counts else 0,
            'std_flags': round(statistics.stdev(flag_counts), 2) if len(flag_counts) > 1 else 0,
            'avg_response_time': round(statistics.mean(response_times), 2) if response_times else 0,
            'median_response_time': round(statistics.median(response_times), 2) if response_times else 0,
            'std_response_time': round(statistics.stdev(response_times), 2) if len(response_times) > 1 else 0,
            'avg_resources': round(statistics.mean(resource_counts), 2) if resource_counts else 0,
            'error_count': error_count,
            'error_rate': round(error_count / n * 100, 1) if n else 0,
            'web_search_count': web_search_count,
            'web_search_rate': round(web_search_count / n * 100, 1) if n else 0,
            'flag_distribution': dict(dim_flags),
            'avg_grounding_pct': round(statistics.mean(grounding_pcts), 1) if grounding_pcts else 0,
            'avg_readability_grade': round(statistics.mean(readability_grades), 1) if readability_grades else 0,
        }

    return analysis


def compute_pairwise_wins(results: dict, corpus: list[dict]) -> dict:
    """For each pair of reasoning levels, count wins across 20 queries."""
    wins = {}

    for i in range(len(REASONING_LEVELS)):
        for j in range(i + 1, len(REASONING_LEVELS)):
            a, b = REASONING_LEVELS[i], REASONING_LEVELS[j]
            a_wins, b_wins, ties = 0, 0, 0

            for query in corpus:
                tid = query['trace_id']
                a_flags = results.get((tid, a), {}).get('eval', {}).get('flag_count', 99)
                b_flags = results.get((tid, b), {}).get('eval', {}).get('flag_count', 99)

                if a_flags < b_flags:
                    a_wins += 1
                elif b_flags < a_flags:
                    b_wins += 1
                else:
                    ties += 1

            wins[f'{a}_vs_{b}'] = {
                f'{a}_wins': a_wins,
                f'{b}_wins': b_wins,
                'ties': ties,
            }

    return wins


def compute_dimension_breakdown(results: dict) -> dict:
    """Which quality dimensions are affected by reasoning level?"""
    # Flag names grouped by dimension
    dim_flag_map = {
        'output_structure': ['INVALID_JSON', 'EMPTY_OUTPUT', 'ZERO_RESOURCES'],
        'resource_count': ['TOO_FEW_RESOURCES', 'EXCESSIVE_RESOURCES'],
        'url_validity': ['BROKEN_URL', 'MANY_MISSING_URLS', 'HOMEPAGE_ONLY'],
        'duplicates': ['DUPLICATE_RESOURCE'],
        'readability': ['ABOVE_8TH_GRADE'],
        'contact_completeness': [],  # MISSING_CONTACT_N is dynamic
        'rag_grounding': ['UNGROUNDED_RESOURCE'],
        'location_match': ['CROSS_STATE'],
        'api_errors': ['API_ERROR'],
    }

    breakdown = {}
    for dim_name, known_flags in dim_flag_map.items():
        breakdown[dim_name] = {}
        for level in REASONING_LEVELS:
            level_results = [v for k, v in results.items() if k[1] == level]
            count = 0
            for r in level_results:
                for flag in r['eval']['flags']:
                    if flag in known_flags:
                        count += 1
                    elif dim_name == 'contact_completeness' and flag.startswith('MISSING_CONTACT_'):
                        count += 1
                    elif dim_name == 'output_structure' and flag.startswith('MISSING_KEYS_'):
                        count += 1
            breakdown[dim_name][level] = count

    return breakdown


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_report(analysis: dict, pairwise: dict, dimension_breakdown: dict,
                    results: dict, corpus: list[dict]) -> str:
    """Generate the markdown comparison report."""
    lines = []
    n = len(corpus)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines.append("# Reasoning Quality Test: Does Reasoning Effort Affect Output Quality?")
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**Model:** {MODEL} | **Temperature:** {TEMPERATURE}")
    lines.append(f"**Prompt:** Production v53 (referral)")
    lines.append(f"**Test queries:** {n}")
    lines.append(f"**Conditions:** {', '.join(REASONING_LEVELS)}")
    lines.append(f"**Total API calls:** {n * len(REASONING_LEVELS)}")
    lines.append("")

    # ------------------------------------------------------------------
    # Executive Summary
    # ------------------------------------------------------------------
    lines.append("## Executive Summary")
    lines.append("")

    # Find best level
    level_scores = [(level, analysis[level]['avg_flags']) for level in REASONING_LEVELS]
    best = min(level_scores, key=lambda x: x[1])
    worst = max(level_scores, key=lambda x: x[1])

    lines.append(f"- **Best quality:** reasoning=\"{best[0]}\" "
                 f"(avg {best[1]} flags/query)")
    lines.append(f"- **Worst quality:** reasoning=\"{worst[0]}\" "
                 f"(avg {worst[1]} flags/query)")

    # Quick speed summary
    fastest = min(REASONING_LEVELS, key=lambda l: analysis[l]['avg_response_time'])
    slowest = max(REASONING_LEVELS, key=lambda l: analysis[l]['avg_response_time'])
    speedup = (analysis[slowest]['avg_response_time'] /
               analysis[fastest]['avg_response_time']) if analysis[fastest]['avg_response_time'] > 0 else 0
    lines.append(f"- **Fastest:** reasoning=\"{fastest}\" "
                 f"({analysis[fastest]['avg_response_time']}s avg)")
    lines.append(f"- **Slowest:** reasoning=\"{slowest}\" "
                 f"({analysis[slowest]['avg_response_time']}s avg, "
                 f"{speedup:.1f}x slower)")
    lines.append("")

    # ------------------------------------------------------------------
    # Quality Flags by Reasoning Level
    # ------------------------------------------------------------------
    lines.append("## Quality Flags by Reasoning Level")
    lines.append("")
    lines.append("| Metric | " + " | ".join(f"reasoning=\"{l}\"" for l in REASONING_LEVELS) + " |")
    lines.append("|--------|" + "|".join(["----------"] * len(REASONING_LEVELS)) + "|")

    rows = [
        ("Total flags", lambda l: str(analysis[l]['total_flags'])),
        ("Avg flags/query", lambda l: f"{analysis[l]['avg_flags']:.2f}"),
        ("Median flags", lambda l: f"{analysis[l]['median_flags']:.1f}"),
        ("Std dev", lambda l: f"{analysis[l]['std_flags']:.2f}"),
        ("Avg resources", lambda l: f"{analysis[l]['avg_resources']:.1f}"),
        ("Avg response time", lambda l: f"{analysis[l]['avg_response_time']:.1f}s"),
        ("Error count", lambda l: f"{analysis[l]['error_count']}/{n}"),
        ("Web search rate", lambda l: f"{analysis[l]['web_search_rate']:.0f}%"),
        ("Avg grounding %", lambda l: f"{analysis[l]['avg_grounding_pct']:.0f}%"),
        ("Avg readability grade", lambda l: f"{analysis[l]['avg_readability_grade']:.1f}"),
    ]

    for label, fn in rows:
        cells = " | ".join(fn(l) for l in REASONING_LEVELS)
        lines.append(f"| {label} | {cells} |")
    lines.append("")

    # ------------------------------------------------------------------
    # Pairwise Win Rates
    # ------------------------------------------------------------------
    lines.append("## Pairwise Win Rates")
    lines.append("")
    lines.append("Win = fewer quality flags on a given query. Lower flags = better quality.")
    lines.append("")
    lines.append("| Comparison | Wins | Losses | Ties |")
    lines.append("|------------|------|--------|------|")

    for pair_key, counts in pairwise.items():
        a, b = pair_key.split('_vs_')
        a_wins = counts[f'{a}_wins']
        b_wins = counts[f'{b}_wins']
        ties = counts['ties']
        lines.append(f"| {a} vs {b} | {a_wins} | {b_wins} | {ties} |")
    lines.append("")

    # ------------------------------------------------------------------
    # Dimension Breakdown
    # ------------------------------------------------------------------
    lines.append("## Dimension Breakdown")
    lines.append("")
    lines.append("Flag counts per dimension by reasoning level "
                 "(lower = better):")
    lines.append("")
    lines.append("| Dimension | " + " | ".join(f"\"{l}\"" for l in REASONING_LEVELS) + " |")
    lines.append("|-----------|" + "|".join(["------"] * len(REASONING_LEVELS)) + "|")

    for dim_name, level_counts in dimension_breakdown.items():
        cells = " | ".join(str(level_counts.get(l, 0)) for l in REASONING_LEVELS)
        lines.append(f"| {dim_name} | {cells} |")
    lines.append("")

    # ------------------------------------------------------------------
    # Speed Comparison
    # ------------------------------------------------------------------
    lines.append("## Speed Comparison")
    lines.append("")
    lines.append("| Level | Avg (s) | Median (s) | Std Dev (s) |")
    lines.append("|-------|---------|------------|-------------|")
    for level in REASONING_LEVELS:
        a = analysis[level]
        lines.append(f"| {level} | {a['avg_response_time']:.1f} | "
                     f"{a['median_response_time']:.1f} | "
                     f"{a['std_response_time']:.1f} |")
    lines.append("")

    # ------------------------------------------------------------------
    # Web Search Rate by Level
    # ------------------------------------------------------------------
    lines.append("## Web Search Rate by Level")
    lines.append("")
    lines.append("| Level | Web Searches | Rate |")
    lines.append("|-------|-------------|------|")
    for level in REASONING_LEVELS:
        a = analysis[level]
        lines.append(f"| {level} | {a['web_search_count']}/{n} | "
                     f"{a['web_search_rate']:.0f}% |")
    lines.append("")

    # ------------------------------------------------------------------
    # Statistical Summary
    # ------------------------------------------------------------------
    lines.append("## Statistical Summary")
    lines.append("")
    lines.append("### Flags per Query")
    lines.append("")
    lines.append("| Level | Mean | Median | Std Dev | Min | Max |")
    lines.append("|-------|------|--------|---------|-----|-----|")
    for level in REASONING_LEVELS:
        level_results = [v for k, v in results.items() if k[1] == level]
        fcs = [r['eval']['flag_count'] for r in level_results]
        if fcs:
            std = statistics.stdev(fcs) if len(fcs) > 1 else 0
            lines.append(f"| {level} | {statistics.mean(fcs):.2f} | "
                         f"{statistics.median(fcs):.1f} | "
                         f"{std:.2f} | "
                         f"{min(fcs)} | {max(fcs)} |")
    lines.append("")

    lines.append("### Response Time (seconds)")
    lines.append("")
    lines.append("| Level | Mean | Median | Std Dev | Min | Max |")
    lines.append("|-------|------|--------|---------|-----|-----|")
    for level in REASONING_LEVELS:
        level_results = [v for k, v in results.items() if k[1] == level]
        rts = [r['api_response']['response_time'] for r in level_results]
        if rts:
            std_rt = statistics.stdev(rts) if len(rts) > 1 else 0
            lines.append(f"| {level} | {statistics.mean(rts):.1f} | "
                         f"{statistics.median(rts):.1f} | "
                         f"{std_rt:.1f} | "
                         f"{min(rts):.1f} | {max(rts):.1f} |")
    lines.append("")

    # ------------------------------------------------------------------
    # Per-Query Results
    # ------------------------------------------------------------------
    lines.append("## Per-Query Results")
    lines.append("")
    lines.append("| Query | " +
                 " | ".join(f"\"{l}\" flags" for l in REASONING_LEVELS) +
                 " | Best |")
    lines.append("|-------|" +
                 "|".join(["--------"] * len(REASONING_LEVELS)) +
                 "|------|")

    for query in corpus:
        tid = query['trace_id']
        query_short = query['user_query'][:35].replace('\n', ' ')
        flag_counts = {}
        for level in REASONING_LEVELS:
            fc = results.get((tid, level), {}).get('eval', {}).get('flag_count', 99)
            flag_counts[level] = fc

        min_flags = min(flag_counts.values())
        winners = [l for l, fc in flag_counts.items() if fc == min_flags]
        best = winners[0] if len(winners) == 1 else "tie"

        cells = " | ".join(str(flag_counts[l]) for l in REASONING_LEVELS)
        lines.append(f"| {query_short}... | {cells} | **{best}** |")
    lines.append("")

    # ------------------------------------------------------------------
    # Conclusion
    # ------------------------------------------------------------------
    lines.append("## Conclusion")
    lines.append("")

    # Determine if there's a meaningful quality difference
    none_flags = analysis['none']['avg_flags']
    other_avgs = {l: analysis[l]['avg_flags'] for l in REASONING_LEVELS if l != 'none'}

    # Check if any level is meaningfully better than none (>10% improvement)
    better_levels = [l for l, avg in other_avgs.items()
                     if avg < none_flags * 0.9]
    worse_levels = [l for l, avg in other_avgs.items()
                    if avg > none_flags * 1.1]

    if better_levels:
        lines.append(f"**Reasoning improves quality.** "
                     f"Level(s) {', '.join(better_levels)} showed meaningfully "
                     f"fewer quality flags than the baseline (reasoning=\"none\").")
    elif worse_levels:
        lines.append(f"**Reasoning hurts quality.** "
                     f"Level(s) {', '.join(worse_levels)} showed meaningfully "
                     f"more quality flags than the baseline, while being slower.")
    else:
        lines.append(f"**Reasoning has no meaningful effect on quality.** "
                     f"All reasoning levels produced similar quality scores, "
                     f"confirming that the additional latency and error risk "
                     f"from higher reasoning provides no quality benefit.")

    lines.append("")

    # Speed penalty summary
    none_time = analysis['none']['avg_response_time']
    for level in ['low', 'medium', 'high']:
        lt = analysis[level]['avg_response_time']
        if none_time > 0:
            ratio = lt / none_time
            lines.append(f"- reasoning=\"{level}\": {ratio:.1f}x slower, "
                         f"{analysis[level]['error_count']} errors")

    lines.append("")
    lines.append("### Recommendation")
    lines.append("")

    if not better_levels:
        lines.append("Use `reasoning=\"none\"` (current production config). "
                     "Higher reasoning levels add latency and failure risk "
                     "with no measurable quality improvement for this use case.")
    else:
        best_level = min(better_levels, key=lambda l: analysis[l]['avg_flags'])
        lines.append(f"Consider `reasoning=\"{best_level}\"` — it shows "
                     f"quality improvement, but weigh against the "
                     f"{analysis[best_level]['avg_response_time'] / none_time:.1f}x "
                     f"latency increase.")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Test reasoning effort effect on output quality")
    parser.add_argument("--skip-url-check", action="store_true",
                        help="Skip HTTP HEAD checks on URLs (faster)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate API calls for testing")
    parser.add_argument("--sample", action="store_true",
                        help="Use sample data instead of production queries")
    parser.add_argument("--levels", type=str, default=None,
                        help="Comma-separated reasoning levels to test (default: all)")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY") and not args.dry_run:
        print("ERROR: Set OPENAI_API_KEY environment variable")
        sys.exit(1)

    print("=" * 80)
    print("REASONING QUALITY TEST")
    print("Does OpenAI reasoning effort affect output quality?")
    print("=" * 80)

    # Load corpus (production by default, --sample for sample data)
    corpus = load_test_corpus(use_production=not args.sample)

    # Override reasoning levels if specified
    global REASONING_LEVELS
    if args.levels:
        REASONING_LEVELS = [l.strip() for l in args.levels.split(',')]
        print(f"Testing levels: {REASONING_LEVELS}")

    # Run experiment
    results = run_experiment(corpus, skip_url_check=args.skip_url_check,
                             dry_run=args.dry_run)

    # Analyze
    print("\n" + "=" * 80)
    print("ANALYZING RESULTS")
    print("=" * 80)

    analysis = analyze_results(results, corpus)
    pairwise = compute_pairwise_wins(results, corpus)
    dimension_breakdown = compute_dimension_breakdown(results)

    # Print quick summary
    print("\nQUICK SUMMARY:")
    print(f"{'Level':<10} {'Avg Flags':<12} {'Avg Time':<12} {'Errors':<8} {'Web Search'}")
    print("-" * 60)
    for level in REASONING_LEVELS:
        a = analysis[level]
        print(f"{level:<10} {a['avg_flags']:<12.2f} {a['avg_response_time']:<12.1f}s "
              f"{a['error_count']:<8} {a['web_search_rate']:.0f}%")

    print("\nPAIRWISE WINS (vs none):")
    for pair_key, counts in pairwise.items():
        if pair_key.startswith('none_vs_'):
            a, b = pair_key.split('_vs_')
            print(f"  none vs {b}: none wins {counts['none_wins']}, "
                  f"{b} wins {counts[f'{b}_wins']}, ties {counts['ties']}")

    # Save raw data
    data_dir = PROJECT_ROOT / 'data'
    data_dir.mkdir(exist_ok=True)

    raw_data = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'model': MODEL,
            'temperature': TEMPERATURE,
            'reasoning_levels': REASONING_LEVELS,
            'total_queries': len(corpus),
            'total_api_calls': len(results),
            'skip_url_check': args.skip_url_check,
        },
        'analysis': analysis,
        'pairwise_wins': pairwise,
        'dimension_breakdown': dimension_breakdown,
        'per_query': [],
    }

    for query in corpus:
        tid = query['trace_id']
        entry = {
            'trace_id': tid,
            'user_query': query['user_query'][:100],
            'prompt_type': query['prompt_type'],
            'results': {},
        }
        for level in REASONING_LEVELS:
            r = results.get((tid, level), {})
            entry['results'][level] = {
                'response_time': r.get('api_response', {}).get('response_time', 0),
                'web_search_used': r.get('api_response', {}).get('web_search_used', False),
                'error': r.get('api_response', {}).get('error'),
                'resource_count': r.get('eval', {}).get('resource_count', 0),
                'flag_count': r.get('eval', {}).get('flag_count', 0),
                'flags': r.get('eval', {}).get('flags', []),
                'content_preview': r.get('api_response', {}).get('content', '')[:500],
            }
        raw_data['per_query'].append(entry)

    raw_path = data_dir / 'reasoning_quality_test_results.json'
    with open(raw_path, 'w') as f:
        json.dump(raw_data, f, indent=2, default=str)
    print(f"\nRaw data saved to: {raw_path}")

    # Generate report
    report = generate_report(analysis, pairwise, dimension_breakdown,
                             results, corpus)

    report_dir = PROJECT_ROOT / 'docs' / 'analysis'
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / 'reasoning_quality_report.md'
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"Report saved to: {report_path}")

    print("\n" + "=" * 80)
    print("DONE")
    print("=" * 80)


if __name__ == '__main__':
    main()
