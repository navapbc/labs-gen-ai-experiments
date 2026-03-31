from __future__ import annotations

"""Phase 5: Generate improvement recommendations from error patterns."""
import json
import logging
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)

# Maps error flags to known prompt improvement strategies
IMPROVEMENT_MAP = {
    'ABOVE_8TH_GRADE': {
        'category': 'Readability',
        'priority': 'HIGH',
        'recommendation': 'Add explicit readability constraints to the prompt: '
                          '"Write all descriptions at an 8th grade reading level or below. '
                          'Use short sentences and common words."',
        'technique': 'Prescriptive word-level bans are more effective than abstract '
                     'readability instructions.',
    },
    'BROKEN_URL': {
        'category': 'URL Accuracy',
        'priority': 'HIGH',
        'recommendation': 'Add URL handling rule: "If you are not certain a specific '
                          'page URL is correct, use the organization homepage URL instead."',
        'technique': 'Homepage-only default >> "use homepage if unsure".',
    },
    'DUPLICATE_RESOURCE': {
        'category': 'Deduplication',
        'priority': 'MEDIUM',
        'recommendation': 'Add dedup rule: "Do NOT include the same organization twice, '
                          'even if it offers multiple relevant services."',
        'technique': 'Named org blocklists >> generic dedup rules.',
    },
    'UNGROUNDED_RESOURCE': {
        'category': 'Grounding',
        'priority': 'HIGH',
        'recommendation': 'Add strict grounding rule: "You MUST only recommend resources '
                          'from the Available Resources list. Do NOT invent or recall resources '
                          'from your training data."',
        'technique': 'Strict grounding ("MUST only use reference list") >> soft preference.',
    },
    'MISSING_CONTACT': {
        'category': 'Contact Info',
        'priority': 'HIGH',
        'recommendation': 'Add pre-submission checklist item: "Every resource MUST have '
                          'at least a phone number OR physical address."',
        'technique': 'Pre-submission checklists catch errors instructions miss.',
    },
    'CROSS_STATE': {
        'category': 'Location',
        'priority': 'MEDIUM',
        'recommendation': 'Add location constraint: "All resources MUST be within the '
                          'client\'s state and ideally within their county."',
        'technique': 'Structural constraints >> behavioral suggestions.',
    },
    'ZERO_RESOURCES': {
        'category': 'Completeness',
        'priority': 'CRITICAL',
        'recommendation': 'Add anti-empty rule: "You MUST return at least one resource. '
                          'NEVER return an empty resources array."',
        'technique': 'Structural constraints ("NEVER empty array") >> behavioral suggestions.',
    },
    'TOO_FEW_RESOURCES': {
        'category': 'Completeness',
        'priority': 'MEDIUM',
        'recommendation': 'Set minimum resource count in prompt: "Aim for 3-7 resources."',
        'technique': 'Explicit numeric bounds work better than vague instructions.',
    },
    'EXCESSIVE_RESOURCES': {
        'category': 'Relevance',
        'priority': 'LOW',
        'recommendation': 'Set maximum resource count: "Return at most 7 resources, '
                          'prioritizing the most relevant."',
        'technique': 'Explicit numeric bounds work better than vague instructions.',
    },
}


def run_improve(config: dict, eval_results: list[dict] | None = None) -> dict:
    """Generate improvement recommendations from error patterns.

    Returns dict with prioritized recommendations.
    """
    output_dir = Path(config['extraction']['output_dir'])

    if eval_results is None:
        eval_path = output_dir / 'eval_results.json'
        if not eval_path.exists():
            raise FileNotFoundError(f"Eval results not found: {eval_path}")
        with open(eval_path) as f:
            eval_results = json.load(f)

    total = len(eval_results)
    logger.info(f"Generating recommendations from {total} eval results")

    # Count flags
    flag_counts = Counter()
    for r in eval_results:
        for f in r.get('flags', []):
            # Normalize MISSING_CONTACT_N to MISSING_CONTACT
            normalized = f.split('_')[0:2]
            if f.startswith('MISSING_CONTACT'):
                flag_counts['MISSING_CONTACT'] += 1
            else:
                flag_counts[f] += 1

    # Generate recommendations
    recommendations = []
    for flag, count in flag_counts.most_common():
        pct = count / total * 100
        improvement = IMPROVEMENT_MAP.get(flag, {
            'category': 'Other',
            'priority': 'LOW',
            'recommendation': f'Investigate and address {flag} errors ({count} occurrences).',
            'technique': 'Review individual flagged traces to identify patterns.',
        })

        recommendations.append({
            'flag': flag,
            'count': count,
            'rate_pct': round(pct, 1),
            **improvement,
        })

    # Sort by priority then count
    priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    recommendations.sort(key=lambda r: (priority_order.get(r['priority'], 4), -r['count']))

    output = {
        'total_traces': total,
        'flagged_traces': sum(1 for r in eval_results if r.get('flag_count', 0) > 0),
        'recommendations': recommendations,
    }

    # Save
    output_path = output_dir / 'recommendations.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    # Generate markdown
    md_path = output_dir / 'recommendations.md'
    with open(md_path, 'w') as f:
        f.write(_generate_md(output))
    logger.info(f"Saved recommendations to {md_path}")

    return output


def _generate_md(output: dict) -> str:
    """Generate markdown recommendations report."""
    lines = [
        "# Prompt Improvement Recommendations",
        "",
        f"Based on automated evaluation of {output['total_traces']} traces.",
        f"Traces with issues: {output['flagged_traces']} "
        f"({output['flagged_traces']/max(output['total_traces'],1)*100:.0f}%)",
        "",
        "## Prioritized Recommendations",
        "",
    ]

    for i, rec in enumerate(output['recommendations']):
        lines.append(f"### {i+1}. [{rec['priority']}] {rec['category']} — {rec['flag']}")
        lines.append(f"- **Occurrences:** {rec['count']} ({rec['rate_pct']}%)")
        lines.append(f"- **Recommendation:** {rec['recommendation']}")
        lines.append(f"- **Technique:** {rec['technique']}")
        lines.append("")

    return '\n'.join(lines)
