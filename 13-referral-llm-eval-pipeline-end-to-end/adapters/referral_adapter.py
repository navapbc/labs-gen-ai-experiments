from __future__ import annotations

"""Adapter for referral/recommendation LLM systems.

Designed for systems that use a pipeline with:
- A root span indicating prompt type
- A ChatPromptBuilder span with input context
- A ReadableLogger span with formatted output
"""
import json
import re
import logging

from adapters.base import TraceAdapter
from lib.trace_parser import parse_attributes

logger = logging.getLogger(__name__)

# Default prompt type mapping — customize via config
DEFAULT_PROMPT_TYPE_MAP = {
    'generate_referrals_rag--centraltx': 'referraltx',
    'generate_referrals_rag--keystone': 'referralkeystone',
    'generate_referrals_rag': 'referral',
    'generate_action_plan': 'actionplan',
}

# Types to skip
SKIP_TYPES = {'email_result', 'email_full_result'}


class ReferralAdapter(TraceAdapter):
    """Adapter for referral pipeline traces."""

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.prompt_type_map = config.get('prompt_type_map', DEFAULT_PROMPT_TYPE_MAP) if config else DEFAULT_PROMPT_TYPE_MAP

    def get_prompt_type(self, spans: list[dict]) -> str | None:
        for span in spans:
            name = span.get('name', '')
            if name in self.prompt_type_map:
                pt = self.prompt_type_map[name]
                if pt in SKIP_TYPES:
                    return None
                return pt
        return None

    def get_user_query(self, spans: list[dict]) -> str:
        query = ''

        # Source 1: Root span input
        for span in spans:
            name = span.get('name', '')
            if name in self.prompt_type_map:
                attrs = parse_attributes(span.get('attributes', {}))
                query = attrs.get('input.value', '') or ''
                if query:
                    break

        # Source 2: ChatPromptBuilder kwargs
        if not query:
            for span in spans:
                if span.get('name') != 'ChatPromptBuilder.run':
                    continue
                attrs = parse_attributes(span.get('attributes', {}))
                input_raw = attrs.get('input.value', '')
                if not input_raw:
                    continue
                try:
                    input_json = json.loads(input_raw)
                    kwargs = input_json.get('kwargs', {})
                    query = kwargs.get('user_query', '') or kwargs.get('query', '') or ''
                    if query:
                        break
                except (json.JSONDecodeError, TypeError):
                    pass

        return query

    def get_output(self, spans: list[dict]) -> tuple[str, dict | None]:
        for span in spans:
            if span.get('name') != 'ReadableLogger.run':
                continue
            attrs = parse_attributes(span.get('attributes', {}))
            raw = attrs.get('output.value', '')
            if raw:
                try:
                    parsed = json.loads(raw)
                    return raw, parsed
                except (json.JSONDecodeError, TypeError):
                    return raw, None
        return '', None

    def get_resources(self, parsed_output: dict) -> list[dict]:
        if not parsed_output or not isinstance(parsed_output, dict):
            return []
        logs = parsed_output.get('logs', [])
        for entry in logs:
            if isinstance(entry, dict) and 'resources' in entry:
                res_list = entry['resources']
                if isinstance(res_list, list):
                    return res_list
        # Fallback: direct resources key
        if 'resources' in parsed_output:
            r = parsed_output['resources']
            return r if isinstance(r, list) else []
        return []

    def get_context(self, spans: list[dict]) -> str:
        for span in spans:
            if span.get('name') != 'ChatPromptBuilder.run':
                continue
            attrs = parse_attributes(span.get('attributes', {}))
            input_raw = attrs.get('input.value', '')
            if not input_raw:
                continue
            try:
                input_json = json.loads(input_raw)
                kwargs = input_json.get('kwargs', {})
                context = kwargs.get('resources', '') or ''
                if not context:
                    supports = kwargs.get('supports', [])
                    if isinstance(supports, list) and supports:
                        context = '\n\n'.join(str(s) for s in supports)
                    elif isinstance(supports, str):
                        context = supports
                if context:
                    return context
            except (json.JSONDecodeError, TypeError):
                pass
        return ''

    def get_metadata(self, spans: list[dict]) -> dict:
        metadata = {}

        # Timestamp from ReadableLogger
        for span in spans:
            if span.get('name') == 'ReadableLogger.run':
                metadata['timestamp'] = span.get('start_time', '')
                break

        # Email from root span
        for span in spans:
            if span.get('name', '') in self.prompt_type_map:
                attrs = parse_attributes(span.get('attributes', {}))
                metadata['email'] = attrs.get('user.id', '') or attrs.get('metadata.user_id', '') or ''
                break

        # Location from query
        query = self.get_user_query(spans)
        metadata['location'] = self._extract_location(query)

        return metadata

    def _extract_location(self, query: str) -> str:
        if not query:
            return ''
        match = re.search(
            r'Focus on resources close to the following location:\s*(.+?)(?:\n|$)',
            query, re.IGNORECASE
        )
        if match:
            return match.group(1).strip()
        match = re.search(r'location:\s*(.+?)(?:\n|$)', query, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ''
