"""Load and validate YAML configuration for the eval pipeline."""
import yaml
from pathlib import Path


DEFAULT_CONFIG = {
    'phoenix': {
        'url': '',
        'api_key': '',
        'project_name': 'default',
        'days_back': 60,
        'max_pages': 100,
    },
    'extraction': {
        'adapter': 'generic',
        'output_dir': 'results',
    },
    'evaluation': {
        'resource_path': 'resources',
        'dimensions': {},
    },
    'sampling': {
        'referral_target': 100,
        'actionplan_target': 50,
        'strata_key': 'prompt_type',
        'seed': 42,
    },
    'analysis': {
        'confidence_level': 0.95,
        'output_path': 'results/eval_report.md',
    },
    'iteration': {
        'model': 'gpt-4o',
        'temperature': 0.7,
        'template_format': 'jinja2',
        'rate_limit_delay': 2.0,
    },
    'optimize': {
        'prompt_name': '',
        'prompt_file': '',
        'test_corpus_path': '',
        'model': 'gpt-4o',
        'temperature': 0.7,
        'template_format': 'jinja2',
        'max_iterations': 5,
        'flag_threshold': 2,
        'auto_deploy': False,
        'improver_model': 'gpt-4o',
    },
}


def load_config(config_path: str) -> dict:
    """Load YAML config and merge with defaults."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path) as f:
        user_config = yaml.safe_load(f) or {}

    config = _deep_merge(DEFAULT_CONFIG, user_config)

    # Resolve paths relative to config file directory
    config_dir = path.parent
    config = _resolve_paths(config, config_dir)

    return config


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _resolve_paths(config: dict, base_dir: Path) -> dict:
    """Resolve relative paths."""
    extraction = config.get('extraction', {})
    if 'output_dir' in extraction:
        p = Path(extraction['output_dir'])
        if not p.is_absolute():
            extraction['output_dir'] = str(base_dir / p)

    analysis = config.get('analysis', {})
    if 'output_path' in analysis:
        p = Path(analysis['output_path'])
        if not p.is_absolute():
            analysis['output_path'] = str(base_dir / p)

    # Resolve iteration version template paths
    iteration = config.get('iteration', {})
    for version in iteration.get('versions', []):
        if 'template_path' in version:
            p = Path(version['template_path'])
            if not p.is_absolute():
                version['template_path'] = str(base_dir / p)

    if 'test_corpus_path' in iteration:
        p = Path(iteration['test_corpus_path'])
        if not p.is_absolute():
            iteration['test_corpus_path'] = str(base_dir / p)

    # Resolve optimize paths
    optimize = config.get('optimize', {})
    for key in ('prompt_file', 'test_corpus_path'):
        if key in optimize and optimize[key]:
            p = Path(optimize[key])
            if not p.is_absolute():
                optimize[key] = str(base_dir / p)

    # Resolve sample data paths
    if 'sample_data' in config:
        sd = config['sample_data']
        for key in ('traces_path', 'eval_results_path'):
            if key in sd:
                p = Path(sd[key])
                if not p.is_absolute():
                    sd[key] = str(base_dir / p)

    return config
