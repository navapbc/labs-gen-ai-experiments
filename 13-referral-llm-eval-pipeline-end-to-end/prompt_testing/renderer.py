"""Template rendering for system prompts.

Supports two modes:
- jinja2: Full Jinja2 template rendering
- plain: Simple {{variable}} replacement via regex
"""
import re

from jinja2 import Environment, BaseLoader


def render_template(template_text: str, variables: dict,
                    template_format: str = 'jinja2') -> str:
    """Render a prompt template with variable substitution.

    Args:
        template_text: The template string.
        variables: Dict of variable names to values.
        template_format: 'jinja2' or 'plain'.

    Returns:
        Rendered string.
    """
    if template_format == 'jinja2':
        return _render_jinja2(template_text, variables)
    elif template_format == 'plain':
        return _render_plain(template_text, variables)
    else:
        raise ValueError(f"Unknown template_format: {template_format}")


def _render_jinja2(template_text: str, variables: dict) -> str:
    """Render using Jinja2 engine."""
    env = Environment(loader=BaseLoader(), keep_trailing_newline=True)
    # Handle undefined variables gracefully
    from jinja2 import Undefined
    env.undefined = _SilentUndefined
    template = env.from_string(template_text)
    return template.render(**variables).strip()


def _render_plain(template_text: str, variables: dict) -> str:
    """Render using simple regex replacement of {{var}} patterns."""
    rendered = template_text
    for key, value in variables.items():
        pattern = r'\{\{\s*' + re.escape(key) + r'\s*\}\}'
        rendered = re.sub(pattern, str(value), rendered)
    return rendered.strip()


class _SilentUndefined:
    """Jinja2 undefined that renders as empty string."""
    def __init__(self, *args, **kwargs):
        pass

    def __str__(self):
        return ''

    def __iter__(self):
        return iter([])

    def __bool__(self):
        return False

    def __getattr__(self, name):
        return self
