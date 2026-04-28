from __future__ import annotations

"""OpenAI API wrapper for prompt simulation."""
import os
import logging

logger = logging.getLogger(__name__)


def call_openai(system_prompt: str, user_prompt: str | None = None,
                model: str = 'gpt-4o', temperature: float = 0.7,
                message_format: str = 'system_only') -> dict:
    """Call OpenAI API with given prompts.

    Args:
        system_prompt: The system message content.
        user_prompt: Optional user message content.
        model: OpenAI model name.
        temperature: Sampling temperature.
        message_format: 'system_only' or 'system_user'.

    Returns:
        Dict with content, model, usage, finish_reason.
    """
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    messages = [{'role': 'system', 'content': system_prompt}]
    if message_format == 'system_user' and user_prompt:
        messages.append({'role': 'user', 'content': user_prompt})

    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
    )

    return {
        'content': response.choices[0].message.content,
        'model': response.model,
        'usage': {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens,
        },
        'finish_reason': response.choices[0].finish_reason,
    }
