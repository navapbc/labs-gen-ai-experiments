"""Load and validate YAML configuration."""
import yaml
from pathlib import Path


DEFAULT_CONFIG = {
    'simulation': {
        'versions': [],
        'test_corpus_path': 'sample_data/test_corpus.json',
        'model': 'gpt-4o',
        'temperature': 0.7,
        'template_format': 'jinja2',
        'message_format': 'system_only',
        'output_dir': 'results',
        'rate_limit_delay': 2.0,
    },
    'evaluation': {
        'resource_path': 'resources',
        'dimensions': {},
    },
    'report': {
        'title': 'Prompt A/B Test Results',
        'output_path': 'results/comparison_report.md',
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
    """Deep merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _resolve_paths(config: dict, base_dir: Path) -> dict:
    """Resolve relative paths in config to absolute paths."""
    sim = config.get('simulation', {})

    # Resolve version template paths (only for local/file-based sources)
    for version in sim.get('versions', []):
        source = version.get('source', 'local')
        if source == 'local' and 'template_path' in version:
            p = Path(version['template_path'])
            if not p.is_absolute():
                version['template_path'] = str(base_dir / p)

    # Resolve test corpus path
    if 'test_corpus_path' in sim:
        p = Path(sim['test_corpus_path'])
        if not p.is_absolute():
            sim['test_corpus_path'] = str(base_dir / p)

    # Resolve output dir
    if 'output_dir' in sim:
        p = Path(sim['output_dir'])
        if not p.is_absolute():
            sim['output_dir'] = str(base_dir / p)

    # Resolve report output path
    report = config.get('report', {})
    if 'output_path' in report:
        p = Path(report['output_path'])
        if not p.is_absolute():
            report['output_path'] = str(base_dir / p)

    return config
