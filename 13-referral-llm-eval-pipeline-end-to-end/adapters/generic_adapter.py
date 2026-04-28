from __future__ import annotations

"""Generic adapter that works with any LLM system.

Finds the longest output span and attempts to parse it as JSON.
Use this as a starting point; write a custom adapter for better results.
"""
import json
import logging

from adapters.base import TraceAdapter
from lib.trace_parser import parse_attributes

logger = logging.getLogger(__name__)


class GenericAdapter(TraceAdapter):
    """Generic adapter — finds longest output span and tries JSON parse."""

    def get_prompt_type(self, spans: list[dict]) -> str | None:
        # Accept all traces; classify by root span name
        if spans:
            return spans[0].get('name', 'unknown')
        return None

    def get_user_query(self, spans: list[dict]) -> str:
        # Look for input.value in any span
        for span in spans:
            attrs = parse_attributes(span.get('attributes', {}))
            input_val = attrs.get('input.value', '')
            if input_val and len(input_val) > 10:
                # Try to extract query from JSON input
                try:
                    input_json = json.loads(input_val)
                    if isinstance(input_json, dict):
                        for key in ('query', 'user_query', 'question', 'prompt', 'input'):
                            if key in input_json:
                                return str(input_json[key])
                        # Check nested kwargs
                        kwargs = input_json.get('kwargs', {})
                        for key in ('query', 'user_query', 'question'):
                            if key in kwargs:
                                return str(kwargs[key])
                except (json.JSONDecodeError, TypeError):
                    pass
                return input_val
        return ''

    def get_output(self, spans: list[dict]) -> tuple[str, dict | None]:
        # Find span with longest output.value
        best_output = ''
        best_parsed = None

        for span in spans:
            attrs = parse_attributes(span.get('attributes', {}))
            output_val = attrs.get('output.value', '')
            if output_val and len(output_val) > len(best_output):
                best_output = output_val
                try:
                    best_parsed = json.loads(output_val)
                except (json.JSONDecodeError, TypeError):
                    best_parsed = None

        return best_output, best_parsed

    def get_resources(self, parsed_output: dict) -> list[dict]:
        if not parsed_output:
            return []

        # Try common resource key patterns
        if isinstance(parsed_output, dict):
            for key in ('resources', 'items', 'results', 'data', 'recommendations'):
                val = parsed_output.get(key)
                if isinstance(val, list):
                    return val

            # Check one level deep
            for key, val in parsed_output.items():
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict):
                            for subkey in ('resources', 'items', 'results'):
                                if subkey in item and isinstance(item[subkey], list):
                                    return item[subkey]

        if isinstance(parsed_output, list):
            return parsed_output

        return []

    def get_metadata(self, spans: list[dict]) -> dict:
        metadata = {}
        if spans:
            metadata['timestamp'] = spans[0].get('start_time', '')
        return metadata
