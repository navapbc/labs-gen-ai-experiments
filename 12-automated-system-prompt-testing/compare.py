#!/usr/bin/env python3
from __future__ import annotations

"""Step 3: Generate comparison report from evaluation results.

Usage:
    python compare.py --config config.yaml
"""
import json
import logging
import argparse
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from lib.config_loader import load_config
from lib.report_generator import compute_metrics, compute_per_query, generate_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def detect_versions(data: list[dict], config: dict) -> list[str]:
    """Detect version names from eval results or config."""
    version_names = [v['name'] for v in config.get('simulation', {}).get('versions', [])]
    if version_names:
        return version_names
    if not data:
        return []
    metadata_keys = {'query_id', 'trace_id', 'user_query', 'location', 'categories'}
    return sorted(k for k in data[0].keys() if k not in metadata_keys
                  and not k.startswith('_') and isinstance(data[0][k], dict))


def main():
    parser = argparse.ArgumentParser(description='Generate comparison report')
    parser.add_argument('--config', required=True, help='Path to YAML config')
    args = parser.parse_args()

    config = load_config(args.config)
    sim_config = config['simulation']
    report_config = config.get('report', {})

    output_dir = Path(sim_config['output_dir'])
    eval_path = output_dir / 'eval_results.json'
    if not eval_path.exists():
        raise FileNotFoundError(f"Eval results not found: {eval_path}. Run evaluate.py first.")

    with open(eval_path) as f:
        eval_results = json.load(f)
    logger.info(f"Loaded {len(eval_results)} eval results")

    versions = detect_versions(eval_results, config)
    logger.info(f"Versions: {versions}")

    metrics = compute_metrics(eval_results, versions)
    per_query = compute_per_query(eval_results, versions)

    report = generate_report(
        metrics, per_query, eval_results, versions,
        title=report_config.get('title', 'Prompt A/B Test Results'),
        model=sim_config.get('model', ''),
        temperature=sim_config.get('temperature', 0),
    )

    report_path = Path(report_config.get('output_path', output_dir / 'comparison_report.md'))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report)
    logger.info(f"Report saved to {report_path}")

    # Print summary
    for i in range(len(versions)):
        for j in range(i + 1, len(versions)):
            va, vb = versions[i], versions[j]
            a_wins = sum(1 for q in per_query if q.get('pairwise', {}).get(f'{va}_vs_{vb}') == va)
            b_wins = sum(1 for q in per_query if q.get('pairwise', {}).get(f'{va}_vs_{vb}') == vb)
            ties = sum(1 for q in per_query if q.get('pairwise', {}).get(f'{va}_vs_{vb}') == 'tie')
            logger.info(f'{va} vs {vb}: {va} wins {a_wins}, {vb} wins {b_wins}, tied {ties}')


if __name__ == '__main__':
    main()
