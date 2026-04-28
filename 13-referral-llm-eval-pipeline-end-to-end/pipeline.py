#!/usr/bin/env python3
"""CLI entry point for the end-to-end LLM evaluation pipeline.

Phases:
    extract   - Pull production traces from Phoenix API
    evaluate  - Run automated quality checks
    sample    - Stratified sampling for deep review
    analyze   - Statistical analysis with confidence intervals
    improve   - Generate improvement recommendations
    iterate   - A/B test prompt changes
    optimize  - Automated prompt optimization loop
    deploy    - Deploy a local prompt file to Phoenix
    run       - Run all phases in sequence

Usage:
    python pipeline.py run --config sample_data/config.yaml
    python pipeline.py extract --config config.yaml
    python pipeline.py optimize --config config.yaml
"""
import sys
import logging
import argparse

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def cmd_extract(args):
    from phases.extract import run_extract
    from lib.config_loader import load_config
    config = load_config(args.config)
    return run_extract(config)


def cmd_evaluate(args):
    from phases.evaluate import run_evaluate
    from lib.config_loader import load_config
    config = load_config(args.config)
    return run_evaluate(config)


def cmd_sample(args):
    from phases.sample import run_sample
    from lib.config_loader import load_config
    config = load_config(args.config)
    return run_sample(config)


def cmd_analyze(args):
    from phases.analyze import run_analyze
    from lib.config_loader import load_config
    config = load_config(args.config)
    return run_analyze(config)


def cmd_improve(args):
    from phases.improve import run_improve
    from lib.config_loader import load_config
    config = load_config(args.config)
    return run_improve(config)


def cmd_iterate(args):
    from phases.iterate import run_iterate
    from lib.config_loader import load_config
    config = load_config(args.config)
    return run_iterate(config)


def cmd_optimize(args):
    from phases.optimize import run_optimize
    from lib.config_loader import load_config
    config = load_config(args.config)
    return run_optimize(config)


def cmd_deploy(args):
    """Deploy a local prompt file to Phoenix."""
    from lib.config_loader import load_config
    from lib.phoenix_prompt_client import PhoenixPromptClient
    from pathlib import Path

    config = load_config(args.config)
    phoenix_url = config.get('phoenix', {}).get('url', '')
    phoenix_key = config.get('phoenix', {}).get('api_key', '')
    client = PhoenixPromptClient(url=phoenix_url, api_key=phoenix_key)

    prompt_file = args.prompt_file
    prompt_name = args.prompt_name
    description = args.description or f'Deployed from {Path(prompt_file).name}'

    path = Path(prompt_file)
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    template_text = path.read_text()

    result = client.deploy_version(
        prompt_name=prompt_name,
        template_text=template_text,
        description=description,
    )
    logger.info(f"Deployed {prompt_file} to Phoenix prompt '{prompt_name}'")
    return result


def cmd_run(args):
    """Run all phases in sequence."""
    from lib.config_loader import load_config
    config = load_config(args.config)

    phases = [
        ('Phase 1: EXTRACT', 'phases.extract', 'run_extract'),
        ('Phase 2: EVALUATE', 'phases.evaluate', 'run_evaluate'),
        ('Phase 3: SAMPLE', 'phases.sample', 'run_sample'),
        ('Phase 4: ANALYZE', 'phases.analyze', 'run_analyze'),
        ('Phase 5: IMPROVE', 'phases.improve', 'run_improve'),
    ]

    # Only include iterate phase if configured
    iter_config = config.get('iteration', {})
    if iter_config.get('versions') and iter_config.get('test_corpus_path'):
        phases.append(('Phase 6: ITERATE', 'phases.iterate', 'run_iterate'))

    results = {}
    for title, module_path, func_name in phases:
        logger.info('')
        logger.info('=' * 60)
        logger.info(title)
        logger.info('=' * 60)

        import importlib
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
        result = func(config)
        results[title] = result

    logger.info('')
    logger.info('=' * 60)
    logger.info('PIPELINE COMPLETE')
    logger.info('=' * 60)

    return results


def main():
    parser = argparse.ArgumentParser(
        description='End-to-end LLM evaluation pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='command', help='Available phases')

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--config', required=True, help='Path to YAML config file')

    subparsers.add_parser('extract', parents=[common], help='Phase 1: Extract traces')
    subparsers.add_parser('evaluate', parents=[common], help='Phase 2: Automated evaluation')
    subparsers.add_parser('sample', parents=[common], help='Phase 3: Stratified sampling')
    subparsers.add_parser('analyze', parents=[common], help='Phase 4: Statistical analysis')
    subparsers.add_parser('improve', parents=[common], help='Phase 5: Improvement recommendations')
    subparsers.add_parser('iterate', parents=[common], help='Phase 6: A/B test prompt changes')
    subparsers.add_parser('optimize', parents=[common], help='Automated prompt optimization loop')

    deploy_parser = subparsers.add_parser('deploy', parents=[common], help='Deploy prompt to Phoenix')
    deploy_parser.add_argument('--prompt-file', required=True, help='Path to prompt text file')
    deploy_parser.add_argument('--prompt-name', required=True, help='Phoenix prompt name')
    deploy_parser.add_argument('--description', default='', help='Version description')

    subparsers.add_parser('run', parents=[common], help='Run all phases')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        'extract': cmd_extract,
        'evaluate': cmd_evaluate,
        'sample': cmd_sample,
        'analyze': cmd_analyze,
        'improve': cmd_improve,
        'iterate': cmd_iterate,
        'optimize': cmd_optimize,
        'deploy': cmd_deploy,
        'run': cmd_run,
    }
    commands[args.command](args)


if __name__ == '__main__':
    main()
