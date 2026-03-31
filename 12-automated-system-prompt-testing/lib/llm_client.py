from __future__ import annotations

"""Multi-provider LLM API wrapper for prompt simulation and variant generation.

Supports:
  - OpenAI models (gpt-*, codex-*, o1-*, o3-*)
  - Anthropic models (claude-*)
"""
import os
import logging

logger = logging.getLogger(__name__)

# Runtime API key overrides (set via web UI)
_openai_api_key_override: str | None = None
_anthropic_api_key_override: str | None = None


def set_openai_api_key(key: str):
    """Set OpenAI API key at runtime (from web UI)."""
    global _openai_api_key_override
    _openai_api_key_override = key


def get_openai_api_key() -> str | None:
    """Get OpenAI API key from runtime override or environment."""
    return _openai_api_key_override or os.environ.get('OPENAI_API_KEY')


def set_anthropic_api_key(key: str):
    """Set Anthropic API key at runtime (from web UI)."""
    global _anthropic_api_key_override
    _anthropic_api_key_override = key


def get_anthropic_api_key() -> str | None:
    """Get Anthropic API key from runtime override or environment."""
    return _anthropic_api_key_override or os.environ.get('ANTHROPIC_API_KEY')


# Map reasoning effort names to OpenAI reasoning_effort parameter values
REASONING_LEVELS = {
    'none': None,
    'low': 'low',
    'medium': 'medium',
    'high': 'high',
}

# Provider detection based on model name prefix
ANTHROPIC_PREFIXES = ('claude-',)
OPENAI_PREFIXES = ('gpt-', 'o1-', 'o3-', 'o4-', 'codex-')


def _detect_provider(model: str) -> str:
    """Detect provider from model name."""
    model_lower = model.lower()
    if model_lower.startswith(ANTHROPIC_PREFIXES):
        return 'anthropic'
    return 'openai'


def call_llm(system_prompt: str, user_prompt: str | None = None,
             model: str = 'gpt-4o', temperature: float = 0.7,
             message_format: str = 'system_only',
             reasoning: str = 'none',
             web_search: bool = False,
             max_tokens: int = 16384) -> dict:
    """Call an LLM API, auto-detecting provider from model name.

    Returns:
        Dict with content, model, usage, finish_reason, web_search_used.
    """
    provider = _detect_provider(model)
    if provider == 'anthropic':
        return _call_anthropic(system_prompt, user_prompt, model, temperature,
                               message_format, max_tokens)
    return call_openai(system_prompt, user_prompt, model, temperature,
                       message_format, reasoning, web_search)


def call_openai(system_prompt: str, user_prompt: str | None = None,
                model: str = 'gpt-4o', temperature: float = 0.7,
                message_format: str = 'system_only',
                reasoning: str = 'none',
                web_search: bool = False) -> dict:
    """Call OpenAI API with given prompts.

    Returns:
        Dict with content, model, usage, finish_reason, web_search_used.
    """
    from openai import OpenAI

    api_key = get_openai_api_key()
    if not api_key:
        raise ValueError(
            'OpenAI API key not configured. Set OPENAI_API_KEY in your '
            '.env file or enter it in the Settings panel in the web UI.'
        )

    client = OpenAI(api_key=api_key)

    if web_search:
        return _call_responses_api(
            client, system_prompt, user_prompt, model, temperature,
            message_format, reasoning,
        )

    # Standard Chat Completions API path
    messages = [{'role': 'system', 'content': system_prompt}]
    if message_format == 'system_user' and user_prompt:
        messages.append({'role': 'user', 'content': user_prompt})

    kwargs = {
        'model': model,
        'temperature': temperature,
        'messages': messages,
    }

    # Add reasoning_effort if not 'none'
    reasoning_effort = REASONING_LEVELS.get(reasoning)
    if reasoning_effort is not None:
        kwargs['reasoning_effort'] = reasoning_effort

    response = client.chat.completions.create(**kwargs)

    return {
        'content': response.choices[0].message.content,
        'model': response.model,
        'usage': {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens,
        },
        'finish_reason': response.choices[0].finish_reason,
        'web_search_used': False,
    }


def _call_responses_api(client, system_prompt, user_prompt, model, temperature,
                        message_format, reasoning):
    """Call OpenAI Responses API with web search tool enabled."""
    if message_format == 'system_user' and user_prompt:
        input_text = user_prompt
    else:
        input_text = 'Respond according to your instructions.'

    kwargs = {
        'model': model,
        'instructions': system_prompt,
        'input': input_text,
        'tools': [{'type': 'web_search_preview'}],
        'temperature': temperature,
    }

    reasoning_effort = REASONING_LEVELS.get(reasoning)
    if reasoning_effort is not None:
        kwargs['reasoning'] = {'effort': reasoning_effort}

    response = client.responses.create(**kwargs)

    web_search_used = False
    content_parts = []

    for item in response.output:
        if item.type == 'web_search_call':
            web_search_used = True
        elif item.type == 'message':
            for block in item.content:
                if hasattr(block, 'text'):
                    content_parts.append(block.text)

    content = '\n'.join(content_parts)

    usage = response.usage
    return {
        'content': content,
        'model': model,
        'usage': {
            'prompt_tokens': getattr(usage, 'input_tokens', 0),
            'completion_tokens': getattr(usage, 'output_tokens', 0),
            'total_tokens': getattr(usage, 'total_tokens',
                                    getattr(usage, 'input_tokens', 0) +
                                    getattr(usage, 'output_tokens', 0)),
        },
        'finish_reason': response.status,
        'web_search_used': web_search_used,
    }


def _call_anthropic(system_prompt: str, user_prompt: str | None,
                    model: str, temperature: float,
                    message_format: str, max_tokens: int) -> dict:
    """Call Anthropic Messages API."""
    import anthropic

    api_key = get_anthropic_api_key()
    if not api_key:
        raise ValueError(
            'Anthropic API key not configured. Set ANTHROPIC_API_KEY in your '
            '.env file or enter it in the Settings panel in the web UI.'
        )

    client = anthropic.Anthropic(api_key=api_key)

    # Build messages — Anthropic requires at least one user message
    if message_format == 'system_user' and user_prompt:
        messages = [{'role': 'user', 'content': user_prompt}]
    else:
        messages = [{'role': 'user', 'content': 'Respond according to your instructions.'}]

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
        temperature=temperature,
    )

    content = ''.join(
        block.text for block in response.content if block.type == 'text'
    )

    return {
        'content': content,
        'model': response.model,
        'usage': {
            'prompt_tokens': response.usage.input_tokens,
            'completion_tokens': response.usage.output_tokens,
            'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
        },
        'finish_reason': response.stop_reason,
        'web_search_used': False,
    }
