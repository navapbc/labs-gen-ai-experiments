#!/usr/bin/env python3
"""Flask web app for prompt A/B testing with Phoenix integration.

Provides a browser UI for:
- Browsing Phoenix prompts and versions
- Editing variant prompts
- Running A/B tests against a test corpus
- Viewing comparison reports
- Deploying winning prompts back to Phoenix
"""
import json
import os
import uuid
import logging
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / 'web' / 'templates'),
    static_folder=str(BASE_DIR / 'web' / 'static'),
)

# In-memory store for test runs and Phoenix settings
_runs: dict[str, dict] = {}
_phoenix_settings: dict[str, str] = {}


def _get_phoenix_client():
    from lib.phoenix_prompt_client import PhoenixPromptClient
    return PhoenixPromptClient(
        url=_phoenix_settings.get('url') or None,
        api_key=_phoenix_settings.get('api_key') or None,
    )


# --- API Routes ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/openai/settings', methods=['GET'])
def api_openai_settings_get():
    """Check if OpenAI API key is configured."""
    from lib.llm_client import get_openai_api_key
    key = get_openai_api_key()
    return jsonify({
        'has_key': bool(key),
        'key_preview': (key[:8] + '...' + key[-4:]) if key and len(key) > 12 else ('***' if key else ''),
        'source': 'env' if os.environ.get('OPENAI_API_KEY') else ('ui' if key else 'none'),
    })


@app.route('/api/openai/settings', methods=['POST'])
def api_openai_settings_set():
    """Set OpenAI API key from the UI."""
    data = request.json
    api_key = data.get('api_key', '').strip()
    if not api_key:
        return jsonify({'error': 'API key is required'}), 400

    from lib.llm_client import set_openai_api_key
    set_openai_api_key(api_key)
    return jsonify({'success': True, 'message': 'OpenAI API key set'})


@app.route('/api/anthropic/settings', methods=['GET'])
def api_anthropic_settings_get():
    """Check if Anthropic API key is configured."""
    from lib.llm_client import get_anthropic_api_key
    key = get_anthropic_api_key()
    return jsonify({
        'has_key': bool(key),
        'key_preview': (key[:8] + '...' + key[-4:]) if key and len(key) > 12 else ('***' if key else ''),
        'source': 'env' if os.environ.get('ANTHROPIC_API_KEY') else ('ui' if key else 'none'),
    })


@app.route('/api/anthropic/settings', methods=['POST'])
def api_anthropic_settings_set():
    """Set Anthropic API key from the UI."""
    data = request.json
    api_key = data.get('api_key', '').strip()
    if not api_key:
        return jsonify({'error': 'API key is required'}), 400

    from lib.llm_client import set_anthropic_api_key
    set_anthropic_api_key(api_key)
    return jsonify({'success': True, 'message': 'Anthropic API key set'})


@app.route('/api/phoenix/settings', methods=['GET'])
def api_phoenix_settings_get():
    """Return current Phoenix connection settings (key is masked)."""
    url = _phoenix_settings.get('url') or os.environ.get('PHOENIX_URL', '')
    key = _phoenix_settings.get('api_key') or os.environ.get('PHOENIX_API_KEY', '')
    return jsonify({
        'url': url,
        'has_key': bool(key),
        'key_preview': (key[:8] + '...' + key[-4:]) if len(key) > 12 else ('***' if key else ''),
        'source': 'ui' if _phoenix_settings.get('url') else ('env' if url else 'none'),
    })


@app.route('/api/phoenix/settings', methods=['POST'])
def api_phoenix_settings_set():
    """Update Phoenix connection settings from the UI."""
    data = request.json
    url = data.get('url', '').strip().rstrip('/')
    api_key = data.get('api_key', '').strip()

    if url:
        _phoenix_settings['url'] = url
    if api_key:
        _phoenix_settings['api_key'] = api_key

    # Quick connectivity test
    try:
        client = _get_phoenix_client()
        prompts = client.list_prompts()
        return jsonify({
            'success': True,
            'message': f'Connected — found {len(prompts)} prompt(s)',
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/phoenix/prompts')
def api_phoenix_prompts():
    """List all Phoenix prompts with version metadata."""
    try:
        client = _get_phoenix_client()
        prompts = client.list_prompts()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'versions': [{
                'id': v.id,
                'sequence_number': v.sequence_number,
                'description': v.description,
                'model_name': v.model_name,
            } for v in p.versions],
        } for p in prompts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/phoenix/version/<path:version_id>')
def api_phoenix_version(version_id):
    """Fetch full template text for a Phoenix prompt version."""
    try:
        client = _get_phoenix_client()
        v = client.get_version(version_id)
        return jsonify({
            'id': v.id,
            'sequence_number': v.sequence_number,
            'description': v.description,
            'model_name': v.model_name,
            'model_provider': v.model_provider,
            'temperature': v.temperature,
            'template_format': v.template_format,
            'template_text': v.template_text,
            'messages': v.messages,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/test-corpus')
def api_test_corpus():
    """List available test corpus files."""
    corpus_files = []
    for pattern in ['sample_data/*.json', 'data/*.json', '*.json']:
        for f in sorted(BASE_DIR.glob(pattern)):
            if f.name.startswith('.') or 'results' in f.parts:
                continue
            try:
                data = json.loads(f.read_text())
                if isinstance(data, list) and len(data) > 0:
                    first = data[0]
                    if isinstance(first, dict) and ('query' in first or 'user_query' in first):
                        corpus_files.append({
                            'path': str(f.relative_to(BASE_DIR)),
                            'count': len(data),
                            'sample_query': first.get('query', first.get('user_query', ''))[:80],
                        })
            except (json.JSONDecodeError, KeyError):
                continue
    return jsonify(corpus_files)


@app.route('/api/run', methods=['POST'])
def api_run():
    """Start a test run in a background thread."""
    data = request.json
    run_id = str(uuid.uuid4())[:8]
    run_state = {
        'id': run_id,
        'status': 'pending',
        'progress': '',
        'config': data,
        'results': None,
        'report': None,
        'error': None,
        'partial': None,
    }
    _runs[run_id] = run_state

    thread = threading.Thread(target=_execute_run, args=(run_id,), daemon=True)
    thread.start()
    return jsonify({'run_id': run_id})


@app.route('/api/run/<run_id>/status')
def api_run_status(run_id):
    """Poll run progress with optional partial results."""
    run = _runs.get(run_id)
    if not run:
        return jsonify({'error': 'Run not found'}), 404
    return jsonify({
        'id': run['id'],
        'status': run['status'],
        'progress': run['progress'],
        'error': run['error'],
        'partial': run.get('partial'),
    })


@app.route('/api/run/<run_id>/results')
def api_run_results(run_id):
    """Get completed run results."""
    run = _runs.get(run_id)
    if not run:
        return jsonify({'error': 'Run not found'}), 404
    if run['status'] != 'completed':
        return jsonify({'error': f"Run status: {run['status']}"}), 400
    return jsonify({
        'report': run['report'],
        'results': run['results'],
    })


@app.route('/api/run/baseline-only', methods=['POST'])
def api_run_baseline_only():
    """Start a baseline-only evaluation run (no variant comparison)."""
    data = request.json
    run_id = str(uuid.uuid4())[:8]
    run_state = {
        'id': run_id,
        'status': 'pending',
        'progress': '',
        'config': {**data, '_baseline_only': True},
        'results': None,
        'report': None,
        'error': None,
        'partial': None,
    }
    _runs[run_id] = run_state

    thread = threading.Thread(target=_execute_run, args=(run_id,), daemon=True)
    thread.start()
    return jsonify({'run_id': run_id})


@app.route('/api/generate-variant', methods=['POST'])
def api_generate_variant():
    """Generate an improved prompt variant using AI analysis of eval failures."""
    data = request.json
    baseline_template = data.get('baseline_template', '')
    eval_summary = data.get('eval_summary', {})
    per_query_flags = data.get('per_query_flags', [])

    if not baseline_template:
        return jsonify({'error': 'baseline_template is required'}), 400

    # Build per-flag fix strategies from proven patterns (v48→v53)
    fix_strategies = {
        'ABOVE_8TH_GRADE': (
            'Add an explicit banned word list: "NEVER use these words in your output: '
            'comprehensive, individualized, utilize, facilitate, encompass, tailored, '
            'Navigate, navigating, holistic, streamline, leverage, multifaceted, '
            'empowerment, proficiency, Additionally, Furthermore, Specifically." '
            'Add: "Write ALL descriptions at a 6th-grade reading level. Use short, '
            'simple sentences. Prefer common words over formal ones."'
        ),
        'BROKEN_URL': (
            'Add: "For every resource URL, ALWAYS use the organization\'s homepage URL '
            '(e.g., https://www.example.org). NEVER construct deep-link or subpage URLs. '
            'If you are not certain a URL is the exact homepage, omit the URL field entirely '
            'rather than guessing."'
        ),
        'DUPLICATE_RESOURCE': (
            'Add: "NEVER include the same organization twice, even if it offers different '
            'programs. Each organization name must appear at most once in your response. '
            'Before outputting, check for duplicate org names and remove any."'
        ),
        'MISSING_CONTACT_PHONE': (
            'Add: "Every resource MUST include a phone number. If the phone number is not '
            'available in the reference data, write \'Phone: Not available — contact via '
            'website\' instead of omitting it."'
        ),
        'MISSING_CONTACT_ADDRESS': (
            'Add: "Every resource MUST include a street address. If the address is not '
            'available in the reference data, write \'Address: Contact organization for '
            'location details\' instead of omitting it."'
        ),
        'MISSING_CONTACT_URL': (
            'Add: "Every resource MUST include a website URL. Use the organization\'s '
            'homepage if no specific program URL is available."'
        ),
        'EMPTY_OUTPUT': (
            'Add: "NEVER return an empty JSON array. If you cannot find matching resources, '
            'return at least 2 general-purpose resources for the user\'s area with a note '
            'explaining limited matches. Add a pre-submission checklist: Before outputting, '
            'verify: 1) Array is not empty, 2) JSON is valid, 3) Each resource has all '
            'required fields."'
        ),
        'INVALID_JSON': (
            'Add: "Your response must be valid JSON only — no markdown, no code fences, '
            'no explanation text. Pre-submission checklist: 1) Response starts with [ or {, '
            '2) All strings are properly quoted, 3) No trailing commas."'
        ),
        'LOW_GROUNDING': (
            'Add: "You MUST only cite organizations that appear in the provided reference '
            'list. NEVER fabricate or invent resource names, addresses, or phone numbers. '
            'If a resource is not in the reference data, do not include it."'
        ),
        'CROSS_STATE': (
            'Add: "Only include resources located in the user\'s state or region. NEVER '
            'include resources from other states, even if they serve similar needs."'
        ),
    }

    # Build the flag analysis section
    flags = eval_summary.get('flags', {})
    total_queries = eval_summary.get('total_queries', 0)
    flag_lines = []
    applicable_fixes = []

    for flag_name, count in sorted(flags.items(), key=lambda x: -x[1]):
        if count > 0:
            flag_lines.append(f'- {flag_name}: {count}/{total_queries} queries affected')
            # Match fix strategies (handle MISSING_CONTACT_* variants)
            if flag_name in fix_strategies:
                applicable_fixes.append(f'**Fix for {flag_name}:** {fix_strategies[flag_name]}')
            elif flag_name.startswith('MISSING_CONTACT_'):
                key = flag_name
                if key in fix_strategies:
                    applicable_fixes.append(f'**Fix for {flag_name}:** {fix_strategies[key]}')

    # Build meta-prompt
    meta_prompt = f"""You are an expert prompt engineer. Your task is to improve an LLM system prompt based on evaluation failures.

## Current Prompt (Baseline)
<baseline_prompt>
{baseline_template}
</baseline_prompt>

## Evaluation Results
The baseline prompt was tested on {total_queries} queries and produced these issues:
{chr(10).join(flag_lines) if flag_lines else '- No flags detected (prompt is performing well)'}

## Proven Fix Strategies
Apply these specific fixes for each issue found:
{chr(10).join(applicable_fixes) if applicable_fixes else 'No specific fixes needed.'}

## Instructions
1. Output ONLY the improved prompt text — no explanations, no markdown wrappers.
2. Preserve the overall structure and intent of the baseline prompt.
3. Integrate the fix strategies naturally into the existing prompt sections.
4. If the prompt already has relevant instructions, strengthen them rather than duplicating.
5. Focus fixes on the highest-count issues first.
6. Keep all existing template variables (like {{{{user_query}}}}, {{{{resources_context}}}}, etc.) intact.
7. Do NOT remove any existing functionality — only add or strengthen instructions.

Output the improved prompt now:"""

    try:
        from lib.llm_client import call_llm
        variant_model = data.get('variant_model', data.get('model', 'gpt-4o'))
        result = call_llm(
            system_prompt=meta_prompt,
            model=variant_model,
            temperature=0.3,
            max_tokens=16384,
        )
        return jsonify({
            'variant_template': result['content'],
            'usage': result['usage'],
            'model_used': result.get('model', variant_model),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/deploy', methods=['POST'])
def api_deploy():
    """Deploy a prompt version to Phoenix."""
    data = request.json
    try:
        client = _get_phoenix_client()
        result = client.deploy_version(
            prompt_name=data['prompt_name'],
            template_text=data['template_text'],
            description=data.get('description', 'Deployed from A/B test UI'),
            model_name=data.get('model_name', 'gpt-5.1'),
            model_provider=data.get('model_provider', 'OPENAI'),
            temperature=data.get('temperature', 0.5),
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- Background run execution ---

def _execute_run(run_id: str):
    """Execute the full simulate -> evaluate -> compare pipeline.

    Evaluates each query inline during simulation so partial results
    can be streamed to the frontend via the status endpoint.
    """
    run = _runs[run_id]
    cfg = run['config']
    baseline_only = cfg.get('_baseline_only', False)

    try:
        run['status'] = 'running'
        run['progress'] = 'Building configuration...'

        # Build a config dict that the pipeline understands
        corpus_path = str(BASE_DIR / cfg['test_corpus_path'])
        output_dir = str(BASE_DIR / 'results' / f'run_{run_id}')
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        versions = [
            {
                'name': 'baseline',
                'source': 'inline',
                'template_text': cfg['baseline_template'],
                'template_format': cfg.get('template_format', 'plain'),
            },
        ]
        if not baseline_only:
            versions.append({
                'name': 'variant',
                'source': 'inline',
                'template_text': cfg['variant_template'],
                'template_format': cfg.get('template_format', 'plain'),
            })

        model = cfg.get('model', 'gpt-4o')
        temperature = cfg.get('temperature', 0.7)
        reasoning = cfg.get('reasoning', 'none')
        web_search = cfg.get('web_search', False)
        version_names = [v['name'] for v in versions]

        # Determine enabled dimensions
        dim_config = {}
        enabled_dims = cfg.get('dimensions', [
            'output_structure', 'resource_count', 'readability',
            'duplicates', 'contact_completeness', 'rag_grounding',
        ])
        for d in enabled_dims:
            dim_config[d] = {'enabled': True}
        if 'url_validity' in enabled_dims:
            dim_config['url_validity'] = {'enabled': True, 'skip_validation': False}
        skip_urls = 'url_validity' not in enabled_dims
        if skip_urls and 'url_validity' in dim_config:
            dim_config['url_validity']['skip_validation'] = True

        pipeline_config = {
            'simulation': {
                'versions': versions,
                'test_corpus_path': corpus_path,
                'model': model,
                'temperature': temperature,
                'reasoning': reasoning,
                'web_search': web_search,
                'template_format': cfg.get('template_format', 'plain'),
                'message_format': cfg.get('message_format', 'system_only'),
                'output_dir': output_dir,
                'rate_limit_delay': cfg.get('rate_limit_delay', 2.0),
            },
            'evaluation': {
                'resource_path': cfg.get('resource_path', 'resources'),
                'dimensions': dim_config,
            },
            'report': {
                'title': 'Web UI A/B Test',
                'output_path': str(Path(output_dir) / 'comparison_report.md'),
            },
        }

        # Pre-load test corpus for inline evaluation context
        corpus_data = json.loads(Path(corpus_path).read_text())
        corpus_lookup = {}
        for q in corpus_data:
            qid = q.get('id', q.get('trace_id', ''))
            if qid:
                corpus_lookup[qid] = q

        # Pre-load evaluation dimensions
        from dimensions.registry import load_dimensions
        from evaluate import evaluate_version
        dimensions = load_dimensions(dim_config)
        resource_path_eval = cfg.get('resource_path', 'resources')

        # Inline evaluation state (built incrementally during simulation)
        eval_results = []
        partial_flag_totals = {}  # "version:FLAG_NAME" -> count

        def on_query_complete(index, total, entry):
            """Evaluate each query immediately as simulation completes it."""
            query_id = entry.get('query_id', '')
            user_query = entry.get('user_query', '')
            location = entry.get('location', '')

            query_data = corpus_lookup.get(query_id, {})
            resources_context = query_data.get('resources_context', '')

            eval_entry = {
                'query_id': query_id,
                'user_query': user_query[:100],
                'location': location,
            }

            for v in version_names:
                v_data = entry.get(v, {})
                v_web_search_used = v_data.get('web_search_used', False)

                context = {
                    'user_query': user_query,
                    'location': location,
                    'resources_context': resources_context,
                    'web_search_used': v_web_search_used,
                }

                eval_entry[v] = evaluate_version(v_data, context, dimensions, resource_path_eval)
                # Carry latency and web_search_used from simulation into eval entry
                eval_entry[v]['latency_ms'] = v_data.get('latency_ms', 0)
                eval_entry[v]['web_search_used'] = v_web_search_used
                for flag in eval_entry[v].get('flags', []):
                    key = f'{v}:{flag}'
                    partial_flag_totals[key] = partial_flag_totals.get(key, 0) + 1

            eval_results.append(eval_entry)

            # Build streaming partial for the frontend
            per_query_partial = []
            for eq in eval_results:
                pq = {'query': eq.get('user_query', ''), 'query_id': eq.get('query_id', '')}
                for v in version_names:
                    pq[f'{v}_flags'] = eq.get(v, {}).get('flag_count', 0)
                    pq[f'{v}_flag_list'] = eq.get(v, {}).get('flags', [])
                    pq[f'{v}_resources'] = eq.get(v, {}).get('resource_count', 0)
                    pq[f'{v}_latency_ms'] = eq.get(v, {}).get('latency_ms', 0)
                    pq[f'{v}_web_search'] = eq.get(v, {}).get('web_search_used', False)
                per_query_partial.append(pq)

            flag_summary = {}
            for v in version_names:
                v_flags = {}
                for k, count in partial_flag_totals.items():
                    if k.startswith(f'{v}:'):
                        v_flags[k[len(f'{v}:'):]] = count
                flag_summary[v] = v_flags

            run['partial'] = {
                'completed': index + 1,
                'total': total,
                'current_query': user_query[:80],
                'per_query': per_query_partial,
                'flag_summary': flag_summary,
                'version_names': version_names,
            }
            run['progress'] = f'Query {index + 1}/{total}: {user_query[:60]}...'

        # Run simulation with inline evaluation callback
        step_total = 1 if baseline_only else 2
        run['progress'] = f'Simulating & evaluating...'
        from simulate import run_simulation
        sim_results = run_simulation(
            pipeline_config, dry_run=False, limit=cfg.get('limit', 0),
            on_query_complete=on_query_complete,
        )

        # Save results to disk
        sim_path = Path(output_dir) / 'simulation_results.json'
        with open(sim_path, 'w') as f:
            json.dump(sim_results, f, indent=2, default=str)

        eval_path = Path(output_dir) / 'eval_results.json'
        with open(eval_path, 'w') as f:
            json.dump(eval_results, f, indent=2, default=str)

        # Compute final metrics from the eval results we built inline
        run['progress'] = 'Computing final metrics...'
        from lib.report_generator import compute_metrics, compute_per_query, generate_report, safe_avg

        metrics = compute_metrics(eval_results, version_names)
        per_query = compute_per_query(eval_results, version_names)

        # Build structured metrics for all modes
        structured_metrics = {}
        for vname in version_names:
            m = metrics.get(vname, {})
            # Gather latency values from eval_results
            latencies = [r.get(vname, {}).get('latency_ms', 0) for r in eval_results
                         if r.get(vname, {}).get('latency_ms')]
            web_search_count = sum(
                1 for r in eval_results
                if r.get(vname, {}).get('web_search_used', False)
            )
            structured_metrics[vname] = {
                'total_flags': sum(m.get('flag_counts', [0])),
                'avg_flags': safe_avg(m.get('flag_counts', [])),
                'flags': dict(m.get('flags', {})),
                'valid_json': m.get('valid_json', 0),
                'total': m.get('total', 0),
                'avg_resources': safe_avg(m.get('resource_counts', [])),
                'avg_grade': safe_avg(m.get('readability_grades', [])),
                'avg_grounding': safe_avg(m.get('grounding_pcts', [])),
                'avg_latency_ms': round(safe_avg(latencies)),
                'p95_latency_ms': round(sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0),
                'web_search_queries': web_search_count,
            }

        # Build per-query structured data (merge latency from eval_results)
        latency_lookup = {}
        for er in eval_results:
            qid = er.get('query_id', '')
            for v in version_names:
                latency_lookup[(qid, v)] = er.get(v, {}).get('latency_ms', 0)

        # Build web_search lookup from eval_results
        web_search_lookup = {}
        for er in eval_results:
            qid = er.get('query_id', '')
            for v in version_names:
                web_search_lookup[(qid, v)] = er.get(v, {}).get('web_search_used', False)

        structured_per_query = []
        for q in per_query:
            trace_id = q.get('trace_id', '')
            entry = {
                'query': q.get('query', ''),
                'trace_id': trace_id,
            }
            for v in version_names:
                entry[f'{v}_flags'] = q.get(f'{v}_flags', 0)
                entry[f'{v}_flag_list'] = q.get(f'{v}_flag_list', [])
                entry[f'{v}_resources'] = q.get(f'{v}_resources', 0)
                entry[f'{v}_latency_ms'] = latency_lookup.get((trace_id, v), 0)
                entry[f'{v}_web_search'] = web_search_lookup.get((trace_id, v), False)
            entry['best'] = q.get('best', 'tie')
            structured_per_query.append(entry)

        if baseline_only:
            # Baseline-only: no comparison report
            run['results'] = {
                'version_names': version_names,
                'query_count': len(eval_results),
                'metrics': structured_metrics,
                'per_query': structured_per_query,
                'baseline_only': True,
            }
            run['report'] = None
        else:
            # Generate comparison report
            run['progress'] = f'Step {step_total}/{step_total}: Generating report...'
            report = generate_report(
                metrics, per_query, eval_results, version_names,
                title='Web UI A/B Test',
                model=model,
                temperature=temperature,
            )

            report_path = Path(output_dir) / 'comparison_report.md'
            with open(report_path, 'w') as f:
                f.write(report)

            # Compute win/loss
            win_loss = {}
            if len(version_names) >= 2:
                va, vb = version_names[0], version_names[1]
                a_wins = sum(1 for q in per_query if q.get('pairwise', {}).get(f'{va}_vs_{vb}') == va)
                b_wins = sum(1 for q in per_query if q.get('pairwise', {}).get(f'{va}_vs_{vb}') == vb)
                ties = len(per_query) - a_wins - b_wins
                win_loss = {
                    'baseline_wins': a_wins,
                    'variant_wins': b_wins,
                    'ties': ties,
                }

            run['results'] = {
                'version_names': version_names,
                'query_count': len(eval_results),
                'metrics': structured_metrics,
                'per_query': structured_per_query,
                'win_loss': win_loss,
                'baseline_only': False,
            }
            run['report'] = report

        run['status'] = 'completed'
        run['progress'] = 'Done'

    except Exception as e:
        logger.exception(f"Run {run_id} failed")
        run['status'] = 'failed'
        run['error'] = str(e)
        run['progress'] = f'Failed: {e}'


def start_app(host='127.0.0.1', port=5001, debug=False, open_browser=True):
    """Start the Flask development server."""
    if open_browser:
        import webbrowser
        threading.Timer(1.5, lambda: webbrowser.open(f'http://{host}:{port}')).start()
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    start_app(debug=True)
