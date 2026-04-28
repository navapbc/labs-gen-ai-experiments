#!/usr/bin/env python3
"""CLI entry point for automated system prompt A/B testing.

Subcommands:
    simulate  - Run prompt versions through LLM
    evaluate  - Run quality dimensions on outputs
    compare   - Generate comparison report
    run       - Run all three steps in sequence
    web       - Launch web UI with Phoenix integration

Usage:
    python prompt_test.py run --config sample_data/config.yaml
    python prompt_test.py run --config sample_data/config.yaml --dry-run
    python prompt_test.py simulate --config config.yaml --limit 3
    python prompt_test.py evaluate --config config.yaml --skip-urls
    python prompt_test.py compare --config config.yaml
    python prompt_test.py web --port 5001
"""
import sys
import json
import logging
import argparse
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def cmd_simulate(args):
    from simulate import run_simulation
    from lib.config_loader import load_config

    config = load_config(args.config)
    results = run_simulation(config, dry_run=args.dry_run, limit=args.limit)

    output_dir = Path(config['simulation']['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'simulation_results.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved {len(results)} results to {output_path}")
    return results


def cmd_evaluate(args):
    from evaluate import run_evaluation
    from lib.config_loader import load_config

    config = load_config(args.config)
    eval_results, versions = run_evaluation(config, skip_urls=args.skip_urls)

    output_dir = Path(config['simulation']['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'eval_results.json'
    with open(output_path, 'w') as f:
        json.dump(eval_results, f, indent=2, default=str)
    logger.info(f"Saved eval results to {output_path}")
    return eval_results, versions


def cmd_compare(args):
    from lib.config_loader import load_config
    from lib.report_generator import compute_metrics, compute_per_query, generate_report

    config = load_config(args.config)
    sim_config = config['simulation']
    report_config = config.get('report', {})

    output_dir = Path(sim_config['output_dir'])
    eval_path = output_dir / 'eval_results.json'
    with open(eval_path) as f:
        eval_results = json.load(f)

    version_names = [v['name'] for v in sim_config.get('versions', [])]
    if not version_names:
        metadata_keys = {'query_id', 'trace_id', 'user_query', 'location', 'categories'}
        version_names = sorted(k for k in eval_results[0].keys() if k not in metadata_keys
                               and not k.startswith('_') and isinstance(eval_results[0][k], dict))

    metrics = compute_metrics(eval_results, version_names)
    per_query = compute_per_query(eval_results, version_names)
    report = generate_report(
        metrics, per_query, eval_results, version_names,
        title=report_config.get('title', 'Prompt A/B Test Results'),
        model=sim_config.get('model', ''),
        temperature=sim_config.get('temperature', 0),
    )

    report_path = Path(report_config.get('output_path', output_dir / 'comparison_report.md'))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report)
    logger.info(f"Report saved to {report_path}")


def cmd_web(args):
    """Launch the web UI for interactive A/B testing."""
    from app import start_app
    logger.info(f'Starting web UI on http://127.0.0.1:{args.port}')
    start_app(port=args.port, debug=args.debug, open_browser=not args.no_browser)


def cmd_run(args):
    """Run all steps: simulate -> evaluate -> compare."""
    logger.info('=' * 60)
    logger.info('STEP 1: SIMULATE')
    logger.info('=' * 60)
    cmd_simulate(args)

    if args.dry_run:
        logger.info('Dry run complete. Skipping evaluate and compare.')
        return

    logger.info('')
    logger.info('=' * 60)
    logger.info('STEP 2: EVALUATE')
    logger.info('=' * 60)
    cmd_evaluate(args)

    logger.info('')
    logger.info('=' * 60)
    logger.info('STEP 3: COMPARE')
    logger.info('=' * 60)
    cmd_compare(args)

    logger.info('')
    logger.info('=' * 60)
    logger.info('DONE')
    logger.info('=' * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Automated system prompt A/B testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Common args
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--config', required=True, help='Path to YAML config file')

    # simulate
    p_sim = subparsers.add_parser('simulate', parents=[common], help='Run prompt simulation')
    p_sim.add_argument('--dry-run', action='store_true', help='Render prompts without API calls')
    p_sim.add_argument('--limit', type=int, default=0, help='Limit number of queries')

    # evaluate
    p_eval = subparsers.add_parser('evaluate', parents=[common], help='Evaluate simulation outputs')
    p_eval.add_argument('--skip-urls', action='store_true', help='Skip URL validation')

    # compare
    subparsers.add_parser('compare', parents=[common], help='Generate comparison report')

    # run (all steps)
    p_run = subparsers.add_parser('run', parents=[common], help='Run all steps')
    p_run.add_argument('--dry-run', action='store_true', help='Render prompts without API calls')
    p_run.add_argument('--limit', type=int, default=0, help='Limit number of queries')
    p_run.add_argument('--skip-urls', action='store_true', help='Skip URL validation')

    # web UI
    p_web = subparsers.add_parser('web', help='Launch web UI for interactive A/B testing')
    p_web.add_argument('--port', type=int, default=5001, help='Port number (default: 5001)')
    p_web.add_argument('--debug', action='store_true', help='Enable Flask debug mode')
    p_web.add_argument('--no-browser', action='store_true', help='Do not auto-open browser')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        'simulate': cmd_simulate,
        'evaluate': cmd_evaluate,
        'compare': cmd_compare,
        'run': cmd_run,
        'web': cmd_web,
    }
    commands[args.command](args)


if __name__ == '__main__':
    main()
