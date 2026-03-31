from __future__ import annotations

"""Phase 3: Stratified sampling for deep review."""
import json
import random
import logging
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


def run_sample(config: dict, traces: list[dict] | None = None,
               eval_results: list[dict] | None = None) -> dict:
    """Select stratified sample for manual/deep review.

    Returns dict with metadata and selected samples.
    """
    output_dir = Path(config['extraction']['output_dir'])
    sample_config = config.get('sampling', {})

    # Load data if not provided
    if traces is None:
        with open(output_dir / 'traces.json') as f:
            traces = json.load(f)
    if eval_results is None:
        eval_path = output_dir / 'eval_results.json'
        if eval_path.exists():
            with open(eval_path) as f:
                eval_results = json.load(f)

    # Identify flagged traces for oversampling
    flagged_ids = set()
    if eval_results:
        flagged_ids = {r['trace_id'] for r in eval_results if r.get('flag_count', 0) > 0}
        logger.info(f"Flagged traces for oversampling: {len(flagged_ids)}")

    strata_key = sample_config.get('strata_key', 'prompt_type')
    seed = sample_config.get('seed', 42)
    target = sample_config.get('referral_target', 100)

    selected = stratified_sample(traces, target, strata_key, flagged_ids, seed)

    output = {
        'metadata': {
            'total_traces': len(traces),
            'sample_size': len(selected),
            'strata_key': strata_key,
            'seed': seed,
        },
        'sample': [
            {
                'trace_id': t['trace_id'],
                'prompt_type': t.get('prompt_type', ''),
                'timestamp': t.get('timestamp', ''),
                'location': t.get('location', ''),
                'resource_count': t.get('resource_count', 0),
                'web_search_used': t.get('web_search_used', ''),
                'is_flagged': t['trace_id'] in flagged_ids,
            }
            for t in selected
        ],
    }

    output_path = output_dir / 'sample.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    logger.info(f"Saved {len(selected)} sampled traces to {output_path}")

    # Generate markdown checklist
    _generate_checklist(selected, flagged_ids, output_dir)

    return output


def stratified_sample(traces: list[dict], target_n: int, strata_key: str,
                      oversample_flagged: set = None, seed: int = 42) -> list[dict]:
    """Select stratified sample from traces."""
    random.seed(seed)

    strata = defaultdict(list)
    for t in traces:
        strata[t.get(strata_key, 'unknown')].append(t)

    total = len(traces)
    if target_n >= total:
        return traces

    # Proportional allocation
    allocation = {}
    remaining = target_n
    for key, group in sorted(strata.items()):
        proportion = len(group) / total
        n = max(1, round(target_n * proportion))
        allocation[key] = min(n, len(group))
        remaining -= allocation[key]

    while remaining > 0:
        for key in sorted(strata.keys()):
            if remaining <= 0:
                break
            if allocation[key] < len(strata[key]):
                allocation[key] += 1
                remaining -= 1

    logger.info(f"Allocation by {strata_key}:")
    for key, n in sorted(allocation.items()):
        logger.info(f"  {key}: {n}/{len(strata[key])}")

    # Select within strata, oversampling flagged
    selected = []
    for key, group in strata.items():
        n = allocation.get(key, 0)
        if n <= 0:
            continue

        if oversample_flagged:
            flagged = [t for t in group if t['trace_id'] in oversample_flagged]
            unflagged = [t for t in group if t['trace_id'] not in oversample_flagged]
            flagged_n = min(len(flagged), n // 2)
            random.shuffle(flagged)
            selected.extend(flagged[:flagged_n])
            remaining_n = n - flagged_n
            random.shuffle(unflagged)
            selected.extend(unflagged[:remaining_n])
        else:
            random.shuffle(group)
            selected.extend(group[:n])

    return selected


def _generate_checklist(selected: list[dict], flagged_ids: set, output_dir: Path):
    """Generate markdown review checklist."""
    lines = ["# Deep Review Checklist", ""]
    for i, t in enumerate(selected):
        flag_marker = " [FLAGGED]" if t['trace_id'] in flagged_ids else ""
        lines.append(f"- [ ] {i+1}. `{t['trace_id'][:12]}...` — {t.get('prompt_type', '?')}"
                     f" — {t.get('location', 'no location')}{flag_marker}")
    lines.append("")
    lines.append(f"**Total: {len(selected)} traces**")

    checklist_path = output_dir / 'review_checklist.md'
    with open(checklist_path, 'w') as f:
        f.write('\n'.join(lines))
    logger.info(f"Saved review checklist to {checklist_path}")
