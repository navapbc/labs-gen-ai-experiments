from __future__ import annotations

"""Phase 6: A/B test prompt changes using bundled prompt testing modules."""
import json
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def run_iterate(config: dict) -> dict | None:
    """Run prompt A/B testing.

    Uses the bundled prompt_testing modules (same as Experiment 12).
    Requires iteration config with versions and test_corpus_path.

    Returns comparison results or None if no iteration config.
    """
    iter_config = config.get('iteration', {})
    versions = iter_config.get('versions', [])
    test_corpus_path = iter_config.get('test_corpus_path')

    if not versions or not test_corpus_path:
        logger.info("No iteration config (versions + test_corpus_path). Skipping.")
        return None

    output_dir = Path(config['extraction']['output_dir'])
    model = iter_config.get('model', 'gpt-4o')
    temperature = iter_config.get('temperature', 0.7)
    template_format = iter_config.get('template_format', 'jinja2')
    rate_limit_delay = iter_config.get('rate_limit_delay', 2.0)

    from prompt_testing.renderer import render_template
    from prompt_testing.llm_client import call_openai
    from prompt_testing.output_parser import parse_json, extract_resources
    from prompt_testing.report_generator import compute_metrics, compute_per_query, generate_report

    # Load templates
    templates = {}
    version_names = []
    for v in versions:
        name = v['name']
        version_names.append(name)
        path = Path(v['template_path'])
        if not path.exists():
            raise FileNotFoundError(f"Template not found for {name}: {path}")
        templates[name] = path.read_text()
        logger.info(f"Loaded template '{name}': {len(templates[name])} chars")

    # Load test corpus
    corpus_path = Path(test_corpus_path)
    if not corpus_path.exists():
        raise FileNotFoundError(f"Test corpus not found: {corpus_path}")
    with open(corpus_path) as f:
        test_corpus = json.load(f)

    resource_path = config.get('evaluation', {}).get('resource_path', 'resources')

    logger.info(f"Running {len(test_corpus)} queries x {len(version_names)} versions")

    # Simulate
    sim_results = []
    for i, query in enumerate(test_corpus):
        query_id = query.get('id', query.get('trace_id', f'query_{i+1:03d}'))
        user_query = query.get('query', query.get('user_query', ''))
        resources_context = query.get('resources_context', '')

        logger.info(f"[{i+1}/{len(test_corpus)}] {query_id}")

        variables = {
            'query': user_query,
            'user_query': user_query,
            'location': query.get('location', ''),
            'resources_context': resources_context,
            'supports': resources_context.split('\n\n') if resources_context else [],
            'response_json': query.get('response_json', '{}'),
        }

        entry = {
            'query_id': query_id,
            'user_query': user_query,
            'location': query.get('location', ''),
            'resources_context_length': len(resources_context),
        }

        for vname in version_names:
            rendered = render_template(templates[vname], variables, template_format)
            try:
                resp = call_openai(rendered, model=model, temperature=temperature)
                parsed, parse_err = parse_json(resp['content'])
                resources = extract_resources(parsed, resource_path)
                entry[vname] = {
                    'raw_content': resp['content'],
                    'parsed_json': parsed,
                    'parse_error': parse_err,
                    'resources': resources,
                    'resource_count': len(resources),
                    'usage': resp['usage'],
                }
            except Exception as e:
                logger.error(f"  {vname} error: {e}")
                entry[vname] = {'error': str(e)}
            time.sleep(1)

        sim_results.append(entry)
        if i < len(test_corpus) - 1:
            time.sleep(rate_limit_delay)

    # Evaluate
    from dimensions.registry import load_dimensions
    dim_config = config.get('evaluation', {}).get('dimensions', {})
    if 'url_validity' in dim_config:
        dim_config['url_validity']['skip_validation'] = True
    dimensions = load_dimensions(dim_config)

    eval_results = []
    for sim in sim_results:
        entry = {
            'query_id': sim['query_id'],
            'user_query': sim['user_query'],
            'location': sim.get('location', ''),
        }
        context = {
            'user_query': sim['user_query'],
            'location': sim.get('location', ''),
            'resources_context': '',
        }

        for vname in version_names:
            v_data = sim.get(vname, {})
            if 'error' in v_data:
                entry[vname] = {'flags': ['API_ERROR'], 'flag_count': 1, 'resource_count': 0}
                continue

            resources = v_data.get('resources', [])
            result = {'flags': [], 'details': {}, 'resource_count': len(resources)}
            dim_context = {**context,
                           'parsed_json': v_data.get('parsed_json'),
                           'parse_error': v_data.get('parse_error'),
                           'raw_content': v_data.get('raw_content', '')}

            for dim in dimensions:
                dr = dim.evaluate(resources, dim_context)
                result['flags'].extend(dr.flags)
                if dr.details:
                    result['details'][dim.name] = dr.details

            result['flag_count'] = len(result['flags'])
            entry[vname] = result

        eval_results.append(entry)

    # Generate report
    metrics = compute_metrics(eval_results, version_names)
    per_query = compute_per_query(eval_results, version_names)
    report = generate_report(
        metrics, per_query, eval_results, version_names,
        title='Prompt Iteration A/B Test',
        model=model, temperature=temperature,
    )

    report_path = output_dir / 'iteration_report.md'
    with open(report_path, 'w') as f:
        f.write(report)
    logger.info(f"Iteration report saved to {report_path}")

    # Save eval results
    iter_eval_path = output_dir / 'iteration_eval.json'
    with open(iter_eval_path, 'w') as f:
        json.dump(eval_results, f, indent=2, default=str)

    return {'eval_results': eval_results, 'metrics': metrics, 'report_path': str(report_path)}


def determine_winner(eval_results: list[dict], version_names: list[str]) -> dict:
    """Determine which version has fewer total flags.

    Args:
        eval_results: List of per-query eval dicts with version sub-dicts.
        version_names: List of version names to compare.

    Returns:
        Dict with 'winner', 'flag_totals', and 'per_version_flags'.
    """
    flag_totals = {}
    per_version_flags = {}

    for vname in version_names:
        total = 0
        all_flags = []
        for r in eval_results:
            v_data = r.get(vname, {})
            flags = v_data.get('flags', [])
            total += len(flags)
            all_flags.extend(flags)
        flag_totals[vname] = total
        per_version_flags[vname] = all_flags

    min_flags = min(flag_totals.values())
    winners = [v for v, count in flag_totals.items() if count == min_flags]
    winner = winners[0] if len(winners) == 1 else version_names[0]  # prefer baseline on tie

    return {
        'winner': winner,
        'flag_totals': flag_totals,
        'per_version_flags': per_version_flags,
    }


def deploy_winner(template_text: str, prompt_name: str, description: str,
                   phoenix_client) -> dict:
    """Deploy the winning prompt version to Phoenix.

    Args:
        template_text: The prompt template text to deploy.
        prompt_name: Phoenix prompt name.
        description: Version description.
        phoenix_client: PhoenixPromptClient instance.

    Returns:
        Deploy response from Phoenix API.
    """
    logger.info(f"Deploying to Phoenix prompt '{prompt_name}': {description}")
    return phoenix_client.deploy_version(
        prompt_name=prompt_name,
        template_text=template_text,
        description=description,
    )
