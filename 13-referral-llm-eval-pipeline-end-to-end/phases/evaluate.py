from __future__ import annotations

"""Phase 2: Automated evaluation using configurable dimensions."""
import json
import logging
from pathlib import Path
from collections import defaultdict

from dimensions.registry import load_dimensions

logger = logging.getLogger(__name__)


def run_evaluate(config: dict, traces: list[dict] | None = None) -> list[dict]:
    """Run automated evaluation on traces.

    Args:
        config: Pipeline config.
        traces: Pre-loaded traces, or None to load from disk.

    Returns:
        List of eval result dicts.
    """
    output_dir = Path(config['extraction']['output_dir'])
    eval_config = config.get('evaluation', {})
    resource_path = eval_config.get('resource_path', 'resources')

    # Load traces if not provided
    if traces is None:
        traces_path = output_dir / 'traces.json'
        if not traces_path.exists():
            raise FileNotFoundError(f"Traces not found: {traces_path}. Run extract phase first.")
        with open(traces_path) as f:
            traces = json.load(f)
    logger.info(f"Evaluating {len(traces)} traces")

    # Load dimensions
    dim_config = eval_config.get('dimensions', {})
    dimensions = load_dimensions(dim_config)
    logger.info(f"Loaded {len(dimensions)} dimensions: {[d.name for d in dimensions]}")

    results = []
    for i, trace in enumerate(traces):
        if (i + 1) % 50 == 0:
            logger.info(f"Processing trace {i+1}/{len(traces)}...")

        result = _evaluate_trace(trace, dimensions)
        results.append(result)

    # Save
    output_path = output_dir / 'eval_results.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved results to {output_path}")

    _print_summary(results)
    return results


def _evaluate_trace(trace: dict, dimensions: list) -> dict:
    """Run all dimensions on a single trace."""
    result = {
        'trace_id': trace.get('trace_id', ''),
        'prompt_type': trace.get('prompt_type', ''),
        'timestamp': trace.get('timestamp', ''),
        'resource_count': trace.get('resource_count', 0),
        'web_search_used': trace.get('web_search_used', ''),
        'flags': [],
        'details': {},
    }

    resources = trace.get('resources', [])
    context = {
        'user_query': trace.get('user_query', ''),
        'location': trace.get('location', ''),
        'resources_context': trace.get('resources_context', ''),
        'parsed_json': trace.get('full_output_json'),
        'raw_content': trace.get('full_output_raw', ''),
    }

    for dim in dimensions:
        dim_result = dim.evaluate(resources, context)
        result['flags'].extend(dim_result.flags)
        if dim_result.details:
            result['details'][dim.name] = dim_result.details

    result['flag_count'] = len(result['flags'])
    return result


def _print_summary(results: list[dict]):
    """Print evaluation summary."""
    total = len(results)
    flagged = sum(1 for r in results if r['flag_count'] > 0)
    logger.info("=" * 50)
    logger.info("EVALUATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total: {total}, Flagged: {flagged} ({flagged/max(total,1)*100:.1f}%)")

    flag_counts = defaultdict(int)
    for r in results:
        for f in r['flags']:
            flag_counts[f] += 1
    for flag, count in sorted(flag_counts.items(), key=lambda x: -x[1]):
        logger.info(f"  {flag}: {count} ({count/total*100:.1f}%)")
