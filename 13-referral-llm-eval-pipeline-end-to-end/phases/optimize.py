from __future__ import annotations

"""Automated prompt optimization loop.

Loads a prompt, evaluates it against a test corpus, generates improved variants
via LLM, A/B tests them, and repeats until convergence.

Convergence criteria:
    - flag_threshold: Stop if total flags <= N (default: 2)
    - max_iterations: Hard cap (default: 5)
    - no-improvement: Stop if variant doesn't beat baseline
"""
import json
import time
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def run_optimize(config: dict) -> dict:
    """Run the optimization loop.

    Loop: load → simulate → evaluate → check threshold → improve → A/B test → pick winner → repeat

    Returns:
        Dict with iteration history, final prompt, and final flag count.
    """
    from prompt_testing.renderer import render_template
    from prompt_testing.llm_client import call_openai
    from prompt_testing.output_parser import parse_json, extract_resources
    from prompt_testing.report_generator import compute_metrics, generate_report
    from dimensions.registry import load_dimensions
    from lib.prompt_improver import build_flag_summary, generate_improved_prompt
    from phases.iterate import determine_winner

    opt_config = config.get('optimize', {})
    output_dir = Path(config['extraction']['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_name = opt_config.get('prompt_name', '')
    prompt_file = opt_config.get('prompt_file', '')
    test_corpus_path = opt_config.get('test_corpus_path', '')
    model = opt_config.get('model', 'gpt-4o')
    temperature = opt_config.get('temperature', 0.7)
    template_format = opt_config.get('template_format', 'jinja2')
    max_iterations = opt_config.get('max_iterations', 5)
    flag_threshold = opt_config.get('flag_threshold', 2)
    auto_deploy = opt_config.get('auto_deploy', False)
    improver_model = opt_config.get('improver_model', 'gpt-4o')
    resource_path = config.get('evaluation', {}).get('resource_path', 'resources')

    if not test_corpus_path:
        raise ValueError("optimize.test_corpus_path is required")

    # Load test corpus
    corpus_path = Path(test_corpus_path)
    if not corpus_path.exists():
        raise FileNotFoundError(f"Test corpus not found: {corpus_path}")
    with open(corpus_path) as f:
        test_corpus = json.load(f)
    logger.info(f"Loaded test corpus: {len(test_corpus)} queries")

    # Load baseline prompt
    baseline_text = _load_prompt(prompt_name, prompt_file, config)
    logger.info(f"Loaded baseline prompt: {len(baseline_text)} chars")

    # Load evaluation dimensions (skip URL validation for speed)
    dim_config = config.get('evaluation', {}).get('dimensions', {})
    if 'url_validity' in dim_config:
        dim_config['url_validity']['skip_validation'] = True
    dimensions = load_dimensions(dim_config)

    # Iteration history
    history = []
    current_prompt = baseline_text

    for iteration in range(1, max_iterations + 1):
        logger.info('')
        logger.info('=' * 60)
        logger.info(f'OPTIMIZATION ITERATION {iteration}/{max_iterations}')
        logger.info('=' * 60)

        # Step 1: Simulate + evaluate current prompt
        logger.info("Simulating current prompt against test corpus...")
        current_eval = _simulate_and_evaluate(
            current_prompt, test_corpus, model, temperature, template_format,
            resource_path, dimensions,
        )

        # Count total flags
        current_flags = sum(
            len(r.get('current', {}).get('flags', []))
            for r in current_eval
        )
        logger.info(f"Current prompt: {current_flags} total flags across {len(test_corpus)} queries")

        # Step 2: Check threshold
        if current_flags <= flag_threshold:
            logger.info(f"Flag count ({current_flags}) <= threshold ({flag_threshold}). CONVERGED!")
            history.append({
                'iteration': iteration,
                'action': 'converged',
                'flags': current_flags,
                'prompt_length': len(current_prompt),
            })
            break

        # Step 3: Generate improved variant
        logger.info("Generating improved variant...")
        flag_summary = build_flag_summary([
            {'flags': r.get('current', {}).get('flags', [])} for r in current_eval
        ])
        improved_text = generate_improved_prompt(
            current_prompt, flag_summary, model=improver_model,
        )

        # Step 4: A/B test — simulate+evaluate both versions
        logger.info("A/B testing current vs improved...")
        ab_eval = _simulate_and_evaluate_ab(
            current_prompt, improved_text, test_corpus, model, temperature,
            template_format, resource_path, dimensions,
        )

        # Step 5: Determine winner
        result = determine_winner(ab_eval, ['current', 'improved'])
        current_total = result['flag_totals']['current']
        improved_total = result['flag_totals']['improved']
        winner = result['winner']

        logger.info(f"Current: {current_total} flags | Improved: {improved_total} flags | Winner: {winner}")

        history.append({
            'iteration': iteration,
            'action': 'ab_test',
            'current_flags': current_total,
            'improved_flags': improved_total,
            'winner': winner,
            'current_prompt_length': len(current_prompt),
            'improved_prompt_length': len(improved_text),
        })

        # Step 6: If no improvement, stop
        if winner == 'current':
            logger.info("No improvement found. STOPPING.")
            history[-1]['action'] = 'no_improvement'
            break

        # Step 7: Winner becomes new baseline
        current_prompt = improved_text
        logger.info(f"Improved prompt adopted as new baseline ({len(current_prompt)} chars)")

    # Save final prompt
    final_path = output_dir / 'optimized_prompt.txt'
    with open(final_path, 'w') as f:
        f.write(current_prompt)
    logger.info(f"Final prompt saved to {final_path}")

    # Save history
    history_path = output_dir / 'optimization_history.json'
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2, default=str)

    # Generate summary report
    report = _generate_optimization_report(history, len(test_corpus), flag_threshold, max_iterations)
    report_path = output_dir / 'optimization_report.md'
    with open(report_path, 'w') as f:
        f.write(report)
    logger.info(f"Optimization report saved to {report_path}")

    # Deploy if configured and prompt changed
    deployed = False
    if current_prompt != baseline_text and prompt_name and auto_deploy:
        try:
            from lib.phoenix_prompt_client import PhoenixPromptClient
            phoenix_url = config.get('phoenix', {}).get('url', '')
            phoenix_key = config.get('phoenix', {}).get('api_key', '')
            client = PhoenixPromptClient(url=phoenix_url, api_key=phoenix_key)
            from phases.iterate import deploy_winner as do_deploy
            final_flags = history[-1].get('improved_flags', history[-1].get('flags', '?'))
            do_deploy(
                current_prompt, prompt_name,
                f"Auto-optimized ({datetime.now():%Y-%m-%d}): {final_flags} flags",
                client,
            )
            deployed = True
            logger.info(f"Deployed optimized prompt to Phoenix: {prompt_name}")
        except Exception as e:
            logger.error(f"Deploy failed: {e}")

    return {
        'iterations': len(history),
        'history': history,
        'final_prompt_path': str(final_path),
        'prompt_changed': current_prompt != baseline_text,
        'deployed': deployed,
    }


def _load_prompt(prompt_name: str, prompt_file: str, config: dict) -> str:
    """Load prompt from Phoenix or local file."""
    # Try Phoenix first
    if prompt_name:
        try:
            from lib.phoenix_prompt_client import PhoenixPromptClient
            phoenix_url = config.get('phoenix', {}).get('url', '')
            phoenix_key = config.get('phoenix', {}).get('api_key', '')
            client = PhoenixPromptClient(url=phoenix_url, api_key=phoenix_key)
            version = client.get_prompt_latest(prompt_name)
            logger.info(f"Loaded prompt '{prompt_name}' v{version.sequence_number} from Phoenix")
            return version.template_text
        except Exception as e:
            logger.warning(f"Could not load from Phoenix: {e}")
            if not prompt_file:
                raise

    # Fall back to local file
    if prompt_file:
        path = Path(prompt_file)
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")
        return path.read_text()

    raise ValueError("Either optimize.prompt_name or optimize.prompt_file is required")


def _simulate_and_evaluate(prompt_text: str, test_corpus: list[dict],
                           model: str, temperature: float, template_format: str,
                           resource_path: str, dimensions: list) -> list[dict]:
    """Simulate a prompt against test corpus and evaluate. Single-version."""
    from prompt_testing.renderer import render_template
    from prompt_testing.llm_client import call_openai
    from prompt_testing.output_parser import parse_json, extract_resources

    results = []
    for i, query in enumerate(test_corpus):
        user_query = query.get('query', query.get('user_query', ''))
        resources_context = query.get('resources_context', '')

        variables = {
            'query': user_query,
            'user_query': user_query,
            'location': query.get('location', ''),
            'resources_context': resources_context,
            'supports': resources_context.split('\n\n') if resources_context else [],
            'response_json': query.get('response_json', '{}'),
        }

        rendered = render_template(prompt_text, variables, template_format)

        entry = {'query_id': query.get('id', f'q{i+1:03d}'), 'user_query': user_query}

        try:
            resp = call_openai(rendered, model=model, temperature=temperature)
            parsed, parse_err = parse_json(resp['content'])
            resources = extract_resources(parsed, resource_path)

            # Evaluate
            flags = []
            details = {}
            context = {
                'user_query': user_query,
                'location': query.get('location', ''),
                'resources_context': resources_context,
                'parsed_json': parsed,
                'parse_error': parse_err,
                'raw_content': resp['content'],
            }
            for dim in dimensions:
                dr = dim.evaluate(resources, context)
                flags.extend(dr.flags)
                if dr.details:
                    details[dim.name] = dr.details

            entry['current'] = {
                'flags': flags,
                'flag_count': len(flags),
                'resource_count': len(resources),
                'details': details,
            }
        except Exception as e:
            logger.error(f"  Query {i+1} error: {e}")
            entry['current'] = {'flags': ['API_ERROR'], 'flag_count': 1, 'resource_count': 0}

        results.append(entry)
        time.sleep(1)

    return results


def _simulate_and_evaluate_ab(current_text: str, improved_text: str,
                               test_corpus: list[dict], model: str,
                               temperature: float, template_format: str,
                               resource_path: str, dimensions: list) -> list[dict]:
    """Simulate two prompt versions against test corpus and evaluate both."""
    from prompt_testing.renderer import render_template
    from prompt_testing.llm_client import call_openai
    from prompt_testing.output_parser import parse_json, extract_resources

    templates = {'current': current_text, 'improved': improved_text}
    version_names = ['current', 'improved']

    results = []
    for i, query in enumerate(test_corpus):
        user_query = query.get('query', query.get('user_query', ''))
        resources_context = query.get('resources_context', '')

        variables = {
            'query': user_query,
            'user_query': user_query,
            'location': query.get('location', ''),
            'resources_context': resources_context,
            'supports': resources_context.split('\n\n') if resources_context else [],
            'response_json': query.get('response_json', '{}'),
        }

        entry = {'query_id': query.get('id', f'q{i+1:03d}'), 'user_query': user_query}

        context = {
            'user_query': user_query,
            'location': query.get('location', ''),
            'resources_context': resources_context,
        }

        for vname in version_names:
            rendered = render_template(templates[vname], variables, template_format)
            try:
                resp = call_openai(rendered, model=model, temperature=temperature)
                parsed, parse_err = parse_json(resp['content'])
                resources = extract_resources(parsed, resource_path)

                flags = []
                details = {}
                dim_context = {
                    **context,
                    'parsed_json': parsed,
                    'parse_error': parse_err,
                    'raw_content': resp['content'],
                }
                for dim in dimensions:
                    dr = dim.evaluate(resources, dim_context)
                    flags.extend(dr.flags)
                    if dr.details:
                        details[dim.name] = dr.details

                entry[vname] = {
                    'flags': flags,
                    'flag_count': len(flags),
                    'resource_count': len(resources),
                    'details': details,
                }
            except Exception as e:
                logger.error(f"  Query {i+1} {vname} error: {e}")
                entry[vname] = {'flags': ['API_ERROR'], 'flag_count': 1, 'resource_count': 0}

            time.sleep(1)

        results.append(entry)

    return results


def _generate_optimization_report(history: list[dict], n_queries: int,
                                   flag_threshold: int, max_iterations: int) -> str:
    """Generate markdown summary of the optimization run."""
    lines = [
        '# Prompt Optimization Report',
        '',
        f'**Generated:** {datetime.now():%Y-%m-%d %H:%M}',
        f'**Test queries:** {n_queries}',
        f'**Flag threshold:** {flag_threshold}',
        f'**Max iterations:** {max_iterations}',
        f'**Iterations run:** {len(history)}',
        '',
        '## Iteration History',
        '',
        '| Iter | Action | Current Flags | Improved Flags | Winner |',
        '|------|--------|---------------|----------------|--------|',
    ]

    for h in history:
        action = h.get('action', '')
        if action == 'converged':
            lines.append(f"| {h['iteration']} | CONVERGED | {h['flags']} | — | — |")
        elif action == 'no_improvement':
            lines.append(
                f"| {h['iteration']} | NO IMPROVEMENT | {h['current_flags']} | "
                f"{h['improved_flags']} | {h['winner']} |"
            )
        else:
            lines.append(
                f"| {h['iteration']} | A/B Test | {h.get('current_flags', '?')} | "
                f"{h.get('improved_flags', '?')} | **{h.get('winner', '?')}** |"
            )

    lines.append('')

    # Final status
    if history:
        last = history[-1]
        action = last.get('action', '')
        if action == 'converged':
            lines.append(f"**Result:** Converged at {last['flags']} flags (threshold: {flag_threshold})")
        elif action == 'no_improvement':
            lines.append(f"**Result:** Stopped — no improvement found at iteration {last['iteration']}")
        else:
            lines.append(f"**Result:** Improved prompt adopted after {len(history)} iterations")

    lines.append('')
    return '\n'.join(lines)
