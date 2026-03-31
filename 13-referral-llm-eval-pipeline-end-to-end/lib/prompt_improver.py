from __future__ import annotations

"""LLM-powered prompt rewriting with proven fix strategies.

Encodes the fix strategies discovered during the v48→v53 iteration cycle
in experiment 12. Uses a meta-prompt to ask an LLM to rewrite a system
prompt based on flag analysis and per-flag fix strategies.
"""
import logging
from collections import Counter

logger = logging.getLogger(__name__)

# Maps flags to concrete prompt-editing strategies proven effective in v48→v53
FIX_STRATEGIES = {
    'ABOVE_8TH_GRADE': (
        'Add a banned-word list: "NEVER use these words: comprehensive, individualized, '
        'utilize, facilitate, subsequently, aforementioned, pertaining, pursuant, '
        'notwithstanding, thereby." Add: "Write every description at a 5th-grade reading '
        'level. Use short sentences (under 15 words). Prefer common words."'
    ),
    'BROKEN_URL': (
        'Add: "ALWAYS use the organization\'s homepage URL (e.g., https://example.org). '
        'NEVER construct deep-link URLs or guess URL paths. If the reference data has a '
        'specific page URL, use it; otherwise default to the homepage."'
    ),
    'HOMEPAGE_ONLY': (
        'The URL check flagged homepage-only URLs. This is usually acceptable behavior. '
        'Only address if the reference data contained specific page URLs that were ignored.'
    ),
    'DUPLICATE_RESOURCE': (
        'Add: "NEVER include the same organization more than once, even if it offers '
        'multiple relevant programs. If an org (e.g., Salvation Army, Caritas) has '
        'multiple branches, pick the ONE closest to the user." Add a named-org blocklist '
        'for known multi-branch orgs in the service area.'
    ),
    'UNGROUNDED_RESOURCE': (
        'Add: "You MUST only recommend resources from the reference list provided. '
        'NEVER fabricate, recall, or invent resources from your training data. If the '
        'reference list has fewer than 3 resources, return only what is available."'
    ),
    'MISSING_CONTACT': (
        'Add a pre-submission checklist: "Before returning, verify EVERY resource has: '
        '(1) a phone number OR (2) a physical address OR (3) a direct URL. If a resource '
        'is missing all three, add them from the reference data or remove the resource."'
    ),
    'CROSS_STATE': (
        'Add: "Only include resources located within the user\'s state and region. '
        'NEVER recommend resources in a different state, even if they serve a similar need."'
    ),
    'ZERO_RESOURCES': (
        'Add: "You MUST return at least one resource. NEVER return an empty resources '
        'array. If the reference list is empty, state that no resources were found but '
        'still return the JSON structure with an empty array and an explanation."'
    ),
    'EMPTY_OUTPUT': (
        'Add structural constraints: "Your response MUST be valid JSON with a \'resources\' '
        'key containing an array. NEVER return plain text or markdown."'
    ),
    'INVALID_JSON': (
        'Add: "Your ENTIRE response must be valid JSON. Do NOT wrap it in markdown code '
        'blocks. Do NOT include any text before or after the JSON object." Add a '
        'pre-submission checklist: "Verify your response is parseable JSON before returning."'
    ),
    'TOO_FEW_RESOURCES': (
        'Add: "Aim to return 3-7 resources. If the reference list has fewer than 3, '
        'return all available resources."'
    ),
    'EXCESSIVE_RESOURCES': (
        'Add: "Return at most 7 resources, prioritizing the most relevant to the user\'s '
        'query. Quality over quantity."'
    ),
}


def build_flag_summary(eval_results: list[dict]) -> dict:
    """Build a structured summary of flags from evaluation results.

    Args:
        eval_results: List of per-query eval dicts, each with a 'flags' key.
            Supports both flat format (flags at top level) and versioned format
            (flags nested under version name keys).

    Returns:
        Dict with total_queries, total_flags, flag_counts (Counter), and
        top_flags (sorted list of (flag, count) tuples).
    """
    flag_counts = Counter()
    total_flags = 0

    for r in eval_results:
        flags = r.get('flags', [])
        # If no top-level flags, look for them in version sub-dicts
        if not flags:
            for key, val in r.items():
                if isinstance(val, dict) and 'flags' in val:
                    flags = val['flags']
                    break
        for f in flags:
            # Normalize MISSING_CONTACT_N → MISSING_CONTACT
            if f.startswith('MISSING_CONTACT_'):
                flag_counts['MISSING_CONTACT'] += 1
            else:
                flag_counts[f] += 1
            total_flags += 1

    return {
        'total_queries': len(eval_results),
        'total_flags': total_flags,
        'flag_counts': flag_counts,
        'top_flags': flag_counts.most_common(),
    }


def generate_improved_prompt(baseline_prompt: str, flag_summary: dict,
                             model: str = 'gpt-4o',
                             temperature: float = 0.3) -> str:
    """Use an LLM to rewrite the baseline prompt to fix flagged issues.

    Args:
        baseline_prompt: Current system prompt text.
        flag_summary: Output of build_flag_summary().
        model: Model to use for prompt rewriting.
        temperature: Low temperature for deterministic rewrites.

    Returns:
        The improved prompt text.
    """
    from prompt_testing.llm_client import call_openai

    if not flag_summary['top_flags']:
        logger.info("No flags to fix — returning baseline unchanged")
        return baseline_prompt

    # Build the fix instructions section
    fix_lines = []
    for flag, count in flag_summary['top_flags']:
        strategy = FIX_STRATEGIES.get(flag, f'Investigate and fix {flag} errors.')
        fix_lines.append(f"- **{flag}** ({count} occurrences): {strategy}")
    fix_instructions = '\n'.join(fix_lines)

    meta_prompt = f"""You are an expert prompt engineer. Your task is to improve a system prompt
for an LLM that generates resource referrals for people in need.

The current prompt was tested against {flag_summary['total_queries']} queries and produced
{flag_summary['total_flags']} total flags (quality issues).

## Current Prompt
<current_prompt>
{baseline_prompt}
</current_prompt>

## Flags Found and Fix Strategies
{fix_instructions}

## Instructions
1. Rewrite the prompt to fix as many flagged issues as possible.
2. Apply EACH fix strategy listed above by adding or modifying the relevant section.
3. Preserve ALL existing functionality — do not remove working instructions.
4. Keep the same template variables ({{{{user_query}}}}, {{{{resources_context}}}}, etc.).
5. Keep the same output JSON structure.
6. Make fixes surgical — add constraints where needed, don't rewrite from scratch.

## Output
Return ONLY the improved prompt text. No explanation, no markdown wrapping, no preamble.
Start directly with the prompt content."""

    logger.info(f"Generating improved prompt with {model} ({len(flag_summary['top_flags'])} flag types to fix)")
    resp = call_openai(meta_prompt, model=model, temperature=temperature)
    improved = resp['content'].strip()

    # Sanity check: improved prompt should be within reasonable length of baseline
    baseline_len = len(baseline_prompt)
    if len(improved) < baseline_len * 0.3:
        logger.warning(f"Improved prompt suspiciously short ({len(improved)} vs {baseline_len} chars)")
    if len(improved) > baseline_len * 3:
        logger.warning(f"Improved prompt suspiciously long ({len(improved)} vs {baseline_len} chars)")

    logger.info(f"Generated improved prompt: {len(improved)} chars (baseline: {baseline_len} chars)")
    return improved
