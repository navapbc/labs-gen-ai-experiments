#!/usr/bin/env python3
from __future__ import annotations

"""Step 2: Run evaluation dimensions on simulation outputs.

Applies configurable quality checks to each version's output.

Usage:
    python evaluate.py --config config.yaml [--skip-urls]
"""
import json
import logging
import argparse
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from lib.config_loader import load_config
from lib.output_parser import extract_resources
from dimensions.registry import load_dimensions

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def detect_versions(sim_results: list[dict], config: dict) -> list[str]:
    """Detect version names from simulation results or config."""
    # Prefer config
    version_names = [v['name'] for v in config.get('simulation', {}).get('versions', [])]
    if version_names:
        return version_names

    # Fall back to auto-detection
    if not sim_results:
        return []
    metadata_keys = {'query_id', 'trace_id', 'user_query', 'location',
                     'resources_context_length', 'categories'}
    return sorted(k for k in sim_results[0].keys() if k not in metadata_keys
                  and not k.startswith('_') and isinstance(sim_results[0][k], dict))


def evaluate_version(version_data: dict, context: dict,
                     dimensions: list, resource_path: str) -> dict:
    """Run all dimensions on a single version's output."""
    result = {'flags': [], 'details': {}}

    if 'error' in version_data:
        result['flags'].append('API_ERROR')
        result['flag_count'] = 1
        result['resource_count'] = 0
        return result

    parsed = version_data.get('parsed_json')
    resources = version_data.get('resources', [])
    if not resources and parsed:
        resources = extract_resources(parsed, resource_path)

    result['resource_count'] = len(resources)

    # Build context for dimensions
    dim_context = {
        **context,
        'parsed_json': parsed,
        'parse_error': version_data.get('parse_error'),
        'raw_content': version_data.get('raw_content', ''),
    }

    for dim in dimensions:
        dim_result = dim.evaluate(resources, dim_context)
        result['flags'].extend(dim_result.flags)
        if dim_result.details:
            result['details'][dim.name] = dim_result.details

    result['flag_count'] = len(result['flags'])
    return result


def run_evaluation(config: dict, skip_urls: bool = False) -> list[dict]:
    """Run evaluation on simulation results."""
    sim_config = config['simulation']
    eval_config = config.get('evaluation', {})
    resource_path = eval_config.get('resource_path', 'resources')

    # Load simulation results
    output_dir = Path(sim_config['output_dir'])
    sim_path = output_dir / 'simulation_results.json'
    if not sim_path.exists():
        raise FileNotFoundError(f"Simulation results not found: {sim_path}. Run simulate.py first.")

    with open(sim_path) as f:
        sim_results = json.load(f)
    logger.info(f"Loaded {len(sim_results)} simulation results")

    versions = detect_versions(sim_results, config)
    logger.info(f"Versions: {versions}")

    # Load test corpus for resources_context
    corpus_path = Path(sim_config['test_corpus_path'])
    query_lookup = {}
    if corpus_path.exists():
        with open(corpus_path) as f:
            corpus = json.load(f)
        for q in corpus:
            qid = q.get('id', q.get('trace_id', ''))
            if qid:
                query_lookup[qid] = q

    # Load dimensions
    dim_config = eval_config.get('dimensions', {})
    if skip_urls and 'url_validity' in dim_config:
        dim_config['url_validity']['skip_validation'] = True
    dimensions = load_dimensions(dim_config)
    logger.info(f"Loaded {len(dimensions)} dimensions: {[d.name for d in dimensions]}")

    eval_results = []

    for i, sim in enumerate(sim_results):
        query_id = sim.get('query_id', sim.get('trace_id', ''))
        user_query = sim.get('user_query', '')
        location = sim.get('location', '')

        # Get resources_context from corpus if available
        query_data = query_lookup.get(query_id, {})
        resources_context = query_data.get('resources_context', '')

        logger.info(f"[{i+1}/{len(sim_results)}] Evaluating {query_id}...")

        entry = {
            'query_id': query_id,
            'user_query': user_query[:100],
            'location': location,
        }

        context = {
            'user_query': user_query,
            'location': location,
            'resources_context': resources_context,
        }

        for v in versions:
            v_data = sim.get(v, {})
            entry[v] = evaluate_version(v_data, context, dimensions, resource_path)

        eval_results.append(entry)

    return eval_results, versions


def main():
    parser = argparse.ArgumentParser(description='Evaluate simulation outputs')
    parser.add_argument('--config', required=True, help='Path to YAML config')
    parser.add_argument('--skip-urls', action='store_true', help='Skip URL validation')
    args = parser.parse_args()

    config = load_config(args.config)
    eval_results, versions = run_evaluation(config, skip_urls=args.skip_urls)

    # Save
    output_dir = Path(config['simulation']['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'eval_results.json'
    with open(output_path, 'w') as f:
        json.dump(eval_results, f, indent=2, default=str)
    logger.info(f"Saved eval results to {output_path}")

    # Summary
    _print_summary(eval_results, versions)


def _print_summary(eval_results, versions):
    """Print evaluation summary."""
    from collections import defaultdict
    n = len(eval_results)
    logger.info('=' * 60)
    logger.info('EVALUATION SUMMARY')
    logger.info('=' * 60)

    for version in versions:
        flag_counts = defaultdict(int)
        total_flags = 0
        for r in eval_results:
            for f in r.get(version, {}).get('flags', []):
                flag_counts[f] += 1
                total_flags += 1

        logger.info(f'\n--- {version} ---')
        logger.info(f'Total flags: {total_flags}')
        for flag, count in sorted(flag_counts.items(), key=lambda x: -x[1]):
            logger.info(f'  {flag}: {count}')

    # Pairwise
    if len(versions) >= 2:
        for i in range(len(versions)):
            for j in range(i + 1, len(versions)):
                va, vb = versions[i], versions[j]
                a_better = sum(1 for r in eval_results
                               if r.get(va, {}).get('flag_count', 99) < r.get(vb, {}).get('flag_count', 99))
                b_better = sum(1 for r in eval_results
                               if r.get(vb, {}).get('flag_count', 99) < r.get(va, {}).get('flag_count', 99))
                tie = n - a_better - b_better
                logger.info(f'\n{va} vs {vb}: {va} wins {a_better}, {vb} wins {b_better}, tied {tie}')


if __name__ == '__main__':
    main()
