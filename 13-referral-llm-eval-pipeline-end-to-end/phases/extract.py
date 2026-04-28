from __future__ import annotations

"""Phase 1: Extract traces from Phoenix API or load from sample data."""
import json
import csv
import logging
from pathlib import Path
from collections import defaultdict

from lib.trace_parser import group_spans_by_trace, extract_traces
from adapters import get_adapter

logger = logging.getLogger(__name__)


def run_extract(config: dict) -> list[dict]:
    """Extract traces from Phoenix or sample data.

    Returns list of trace dicts.
    """
    output_dir = Path(config['extraction']['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for sample data first
    sample_data = config.get('sample_data', {})
    traces_path = sample_data.get('traces_path')
    if traces_path and Path(traces_path).exists():
        logger.info(f"Loading traces from sample data: {traces_path}")
        with open(traces_path) as f:
            traces = json.load(f)
        logger.info(f"Loaded {len(traces)} traces from sample data")
        _save_traces(traces, output_dir)
        return traces

    # Fetch from Phoenix API
    phoenix_config = config.get('phoenix', {})
    from lib.phoenix_client import PhoenixClient

    client = PhoenixClient(
        url=phoenix_config.get('url'),
        api_key=phoenix_config.get('api_key'),
        project_name=phoenix_config.get('project_name', 'default'),
    )

    all_spans = client.fetch_spans(
        days_back=phoenix_config.get('days_back', 60),
        max_pages=phoenix_config.get('max_pages', 100),
    )

    if not all_spans:
        logger.error("No spans fetched from Phoenix")
        return []

    # Group and extract
    grouped = group_spans_by_trace(all_spans)
    logger.info(f"Found {len(grouped)} unique traces")

    adapter_name = config['extraction'].get('adapter', 'generic')
    adapter = get_adapter(adapter_name, config=config.get('adapter_config'))

    traces = extract_traces(grouped, adapter)
    _save_traces(traces, output_dir)
    _print_summary(traces)

    return traces


def _save_traces(traces: list[dict], output_dir: Path):
    """Save traces to JSON and CSV."""
    json_path = output_dir / 'traces.json'
    with open(json_path, 'w') as f:
        json.dump(traces, f, indent=2, default=str)
    logger.info(f"Saved {len(traces)} traces to {json_path}")

    # CSV summary
    csv_path = output_dir / 'traces.csv'
    if traces:
        csv_fields = ['trace_id', 'timestamp', 'prompt_type', 'resource_count',
                       'web_search_used', 'span_count']
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction='ignore')
            writer.writeheader()
            for t in traces:
                writer.writerow(t)
        logger.info(f"Saved CSV summary to {csv_path}")


def _print_summary(traces: list[dict]):
    """Print extraction summary."""
    logger.info("=" * 50)
    logger.info("EXTRACTION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total traces: {len(traces)}")

    type_counts = defaultdict(int)
    for t in traces:
        type_counts[t.get('prompt_type', 'unknown')] += 1
    logger.info(f"By type: {dict(type_counts)}")

    with_output = sum(1 for t in traces if t.get('full_output_json'))
    logger.info(f"Traces with output: {with_output}/{len(traces)}")
