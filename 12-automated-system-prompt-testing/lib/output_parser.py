from __future__ import annotations

"""Parse JSON output from LLM responses."""
import json
import re


def parse_json(raw_content: str) -> tuple[dict | None, str | None]:
    """Try to parse JSON from model response.

    Handles:
    - Direct JSON
    - JSON in markdown code blocks
    - JSON extracted from first { to last }

    Returns:
        Tuple of (parsed_dict_or_none, error_message_or_none).
    """
    if not raw_content:
        return None, 'Empty response'

    # Try direct parse
    try:
        return json.loads(raw_content), None
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    code_block = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw_content, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1)), None
        except json.JSONDecodeError:
            pass

    # Try first { to last }
    first_brace = raw_content.find('{')
    last_brace = raw_content.rfind('}')
    if first_brace >= 0 and last_brace > first_brace:
        try:
            return json.loads(raw_content[first_brace:last_brace + 1]), None
        except json.JSONDecodeError:
            pass

    # Try first [ to last ] (for top-level arrays)
    first_bracket = raw_content.find('[')
    last_bracket = raw_content.rfind(']')
    if first_bracket >= 0 and last_bracket > first_bracket:
        try:
            return json.loads(raw_content[first_bracket:last_bracket + 1]), None
        except json.JSONDecodeError:
            pass

    return None, f'Could not parse JSON from response ({len(raw_content)} chars)'


def extract_resources(parsed_json: dict | None, resource_path: str = 'resources') -> list[dict]:
    """Extract resources list from parsed output.

    Args:
        parsed_json: Parsed JSON output.
        resource_path: Dot-separated path to resources array.
            Examples: 'resources', 'logs.resources', 'data.items'

    Returns:
        List of resource dicts.
    """
    if not parsed_json:
        return []

    # If the top-level IS already a list of resource dicts, return it directly
    if isinstance(parsed_json, list):
        if len(parsed_json) > 0 and isinstance(parsed_json[0], dict):
            # Check if items look like resources (have 'name' key)
            if 'name' in parsed_json[0]:
                return parsed_json
        return []

    # Navigate dot-separated path for dict-wrapped responses
    parts = resource_path.split('.')
    current = parsed_json

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list):
            # Search through list items for the key
            for item in current:
                if isinstance(item, dict) and part in item:
                    current = item[part]
                    break
            else:
                return []
        else:
            return []

    if isinstance(current, list):
        return current

    return []
