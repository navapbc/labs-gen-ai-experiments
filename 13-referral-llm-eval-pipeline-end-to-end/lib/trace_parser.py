from __future__ import annotations

"""Group spans into traces and extract data using adapters."""
import ast
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def parse_attributes(attrs):
    """Safely parse attributes that may be string or dict."""
    if isinstance(attrs, str):
        try:
            return ast.literal_eval(attrs)
        except Exception:
            return {}
    return attrs if isinstance(attrs, dict) else {}


def parse_context(ctx):
    """Safely parse context that may be string or dict."""
    if isinstance(ctx, str):
        try:
            return ast.literal_eval(ctx)
        except Exception:
            return {}
    return ctx if isinstance(ctx, dict) else {}


def group_spans_by_trace(all_spans: list[dict]) -> dict[str, list[dict]]:
    """Group spans by trace_id."""
    traces = defaultdict(list)
    for span in all_spans:
        ctx = parse_context(span.get('context', {}))
        trace_id = ctx.get('trace_id', '')
        if trace_id:
            traces[trace_id].append(span)
    return dict(traces)


def extract_traces(grouped_spans: dict[str, list[dict]], adapter) -> list[dict]:
    """Extract trace data using the provided adapter.

    Args:
        grouped_spans: Dict mapping trace_id to list of spans.
        adapter: TraceAdapter instance.

    Returns:
        List of extracted trace dicts.
    """
    extracted = []
    skipped = 0

    for trace_id, spans in grouped_spans.items():
        try:
            prompt_type = adapter.get_prompt_type(spans)
            if prompt_type is None:
                skipped += 1
                continue

            user_query = adapter.get_user_query(spans)
            raw_output, parsed_output = adapter.get_output(spans)
            resources = adapter.get_resources(parsed_output) if parsed_output else []
            context = adapter.get_context(spans)
            metadata = adapter.get_metadata(spans)

            trace_data = {
                'trace_id': trace_id,
                'timestamp': metadata.get('timestamp', ''),
                'prompt_type': prompt_type,
                'user_query': user_query,
                'location': metadata.get('location', ''),
                'full_output_raw': raw_output,
                'full_output_json': parsed_output,
                'resources': resources,
                'resource_count': len(resources),
                'resources_context': context,
                'web_search_used': metadata.get('web_search_used', 'UNKNOWN'),
                'span_count': len(spans),
                **{k: v for k, v in metadata.items()
                   if k not in ('timestamp', 'location', 'web_search_used')},
            }
            extracted.append(trace_data)
        except Exception as e:
            logger.warning(f"Error extracting trace {trace_id}: {e}")
            skipped += 1

    logger.info(f"Extracted {len(extracted)} traces, skipped {skipped}")
    return extracted
