from __future__ import annotations

"""Phoenix Prompt API client.

Reads prompt metadata and templates via GraphQL, deploys new versions via REST.
"""
import os
import logging
import warnings
from dataclasses import dataclass, field

import httpx

warnings.filterwarnings('ignore', message='.*Unverified HTTPS.*')

logger = logging.getLogger(__name__)


@dataclass
class PromptVersion:
    id: str
    sequence_number: int
    description: str = ''
    model_name: str = ''
    model_provider: str = ''
    temperature: float = 0.7
    template_format: str = 'MUSTACHE'
    messages: list[dict] = field(default_factory=list)

    @property
    def template_text(self) -> str:
        """Extract system message content from messages list."""
        for msg in self.messages:
            if msg.get('role') == 'system':
                return msg.get('content', '')
        return self.messages[0].get('content', '') if self.messages else ''


@dataclass
class Prompt:
    id: str
    name: str
    description: str = ''
    versions: list[PromptVersion] = field(default_factory=list)


class PhoenixPromptClient:
    """Client for Phoenix prompt management API."""

    def __init__(self, url: str | None = None, api_key: str | None = None):
        self.url = (url or os.getenv('PHOENIX_URL', '')).rstrip('/')
        self.api_key = api_key or os.getenv('PHOENIX_API_KEY', '')
        if not self.url:
            raise ValueError('PHOENIX_URL not set')
        self._client = httpx.Client(
            headers={'Authorization': f'Bearer {self.api_key}'},
            verify=False,
            timeout=30,
        )

    def _graphql(self, query: str, variables: dict | None = None) -> dict:
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        resp = self._client.post(f'{self.url}/graphql', json=payload)
        resp.raise_for_status()
        data = resp.json()
        if 'errors' in data:
            raise RuntimeError(f"GraphQL errors: {data['errors']}")
        return data['data']

    def _fetch_prompts_full(self) -> list[Prompt]:
        """Fetch all prompts with full version data including template content.

        Uses a single prompts query with nested promptVersions to avoid the
        node(id: GlobalID!) query which is buggy on Phoenix v10.9.1.
        """
        query = '''
        {
          prompts(first: 50) {
            edges {
              node {
                id
                name
                description
                promptVersions(first: 10) {
                  edges {
                    node {
                      id
                      sequenceNumber
                      description
                      modelName
                      modelProvider
                      templateFormat
                      invocationParameters
                      template {
                        __typename
                      }
                    }
                  }
                }
              }
            }
          }
        }
        '''
        data = self._graphql(query)
        prompts = []
        for edge in data.get('prompts', {}).get('edges', []):
            node = edge['node']
            versions = []
            for v_edge in node.get('promptVersions', {}).get('edges', []):
                v = v_edge['node']
                temperature = 0.7
                inv_params = v.get('invocationParameters')
                if isinstance(inv_params, dict):
                    openai_params = inv_params.get('openai', {})
                    temperature = openai_params.get('temperature', 0.7)
                versions.append(PromptVersion(
                    id=v['id'],
                    sequence_number=v['sequenceNumber'],
                    description=v.get('description', ''),
                    model_name=v.get('modelName', ''),
                    model_provider=v.get('modelProvider', ''),
                    temperature=temperature,
                    template_format=v.get('templateFormat', 'MUSTACHE'),
                ))
            prompts.append(Prompt(
                id=node['id'],
                name=node['name'],
                description=node.get('description', ''),
                versions=versions,
            ))
        return prompts

    def list_prompts(self) -> list[Prompt]:
        """List all prompts with their version metadata."""
        return self._fetch_prompts_full()

    def get_version(self, version_id: str) -> PromptVersion:
        """Fetch full template content for a specific version by its global ID.

        Uses the REST API (GET /v1/prompt_versions/{id}) since the GraphQL
        node(id: GlobalID!) query is broken on Phoenix v10.9.1.
        Falls back to a per-prompt GraphQL traversal if REST fails.
        """
        # Strategy 1: REST API (works on newer Phoenix)
        try:
            resp = self._client.get(f'{self.url}/v1/prompt_versions/{version_id}')
            if resp.status_code == 200:
                d = resp.json().get('data', resp.json())
                messages = []
                tmpl = d.get('template', {})
                if isinstance(tmpl, dict) and 'messages' in tmpl:
                    messages = [{'role': m.get('role', 'system'), 'content': m.get('content', '')}
                                for m in tmpl['messages']]
                temperature = 0.7
                inv = d.get('invocation_parameters') or d.get('invocationParameters', {})
                if isinstance(inv, dict):
                    temperature = inv.get('openai', {}).get('temperature', 0.7)
                return PromptVersion(
                    id=d.get('id', version_id),
                    sequence_number=d.get('sequence_number', d.get('sequenceNumber', 0)),
                    description=d.get('description', ''),
                    model_name=d.get('model_name', d.get('modelName', '')),
                    model_provider=d.get('model_provider', d.get('modelProvider', '')),
                    temperature=temperature,
                    template_format=d.get('template_format', d.get('templateFormat', 'MUSTACHE')),
                    messages=messages,
                )
        except Exception as e:
            logger.debug(f"REST prompt_versions lookup failed: {e}")

        # Strategy 2: Fetch via per-prompt GraphQL query that includes template messages
        # Walk each prompt's versions to find the matching version_id
        query = '''
        {
          prompts(first: 50) {
            edges {
              node {
                name
                promptVersions(first: 10) {
                  edges {
                    node {
                      id
                      sequenceNumber
                      description
                      modelName
                      modelProvider
                      templateFormat
                      invocationParameters
                      template {
                        __typename
                      }
                    }
                  }
                }
              }
            }
          }
        }
        '''
        data = self._graphql(query)
        # Find the version, then fetch its template content via the prompt-specific query
        for p_edge in data.get('prompts', {}).get('edges', []):
            p_node = p_edge['node']
            for v_edge in p_node.get('promptVersions', {}).get('edges', []):
                v = v_edge['node']
                if v['id'] == version_id:
                    # Found it — now fetch the template text via REST prompt endpoint
                    prompt_name = p_node['name']
                    seq = v['sequenceNumber']
                    return self._fetch_version_via_rest_prompt(
                        prompt_name, seq, v
                    )
        raise ValueError(f"Version {version_id} not found")

    def _fetch_version_via_rest_prompt(
        self, prompt_name: str, seq: int, version_meta: dict
    ) -> PromptVersion:
        """Fetch a specific prompt version's template text via REST GET /v1/prompts/{name}.

        The REST endpoint returns the latest version with full template content.
        For non-latest versions, we POST a new lookup or use cached data.
        """
        # Try REST: GET /v1/prompts/<name>/versions/<seq> or similar
        # Phoenix REST usually returns latest on GET /v1/prompts/<name>
        resp = self._client.get(f'{self.url}/v1/prompts/{prompt_name}')
        if resp.status_code == 200:
            d = resp.json().get('data', resp.json())
            ver_data = d.get('version', d)
            rest_seq = ver_data.get('sequence_number', ver_data.get('sequenceNumber', 0))

            if rest_seq == seq:
                messages = []
                tmpl = ver_data.get('template', {})
                if isinstance(tmpl, dict) and 'messages' in tmpl:
                    messages = [{'role': m.get('role', 'system'), 'content': m.get('content', '')}
                                for m in tmpl['messages']]
                temperature = 0.7
                inv = ver_data.get('invocation_parameters', ver_data.get('invocationParameters', {}))
                if isinstance(inv, dict):
                    temperature = inv.get('openai', {}).get('temperature', 0.7)
                return PromptVersion(
                    id=version_meta.get('id', ''),
                    sequence_number=seq,
                    description=version_meta.get('description', ''),
                    model_name=version_meta.get('modelName', ''),
                    model_provider=version_meta.get('modelProvider', ''),
                    temperature=temperature,
                    template_format=version_meta.get('templateFormat', 'MUSTACHE'),
                    messages=messages,
                )

        # If we can't get the specific version's template, return metadata-only
        # with an informative error in template_text
        temperature = 0.7
        inv = version_meta.get('invocationParameters', {})
        if isinstance(inv, dict):
            temperature = inv.get('openai', {}).get('temperature', 0.7)

        raise ValueError(
            f"Could not fetch template for {prompt_name} v{seq}. "
            f"Only the latest version is available via REST. "
            f"Select the latest version or paste the template manually."
        )

    def get_prompt_latest(self, prompt_name: str) -> PromptVersion:
        """Get the latest version of a prompt by name.

        Uses REST GET /v1/prompts/{name} which returns the latest version
        with full template content.
        """
        resp = self._client.get(f'{self.url}/v1/prompts/{prompt_name}')
        if resp.status_code == 200:
            d = resp.json().get('data', resp.json())
            ver = d.get('version', d)
            messages = []
            tmpl = ver.get('template', {})
            if isinstance(tmpl, dict) and 'messages' in tmpl:
                messages = [{'role': m.get('role', 'system'), 'content': m.get('content', '')}
                            for m in tmpl['messages']]
            temperature = 0.7
            inv = ver.get('invocation_parameters', ver.get('invocationParameters', {}))
            if isinstance(inv, dict):
                temperature = inv.get('openai', {}).get('temperature', 0.7)
            return PromptVersion(
                id=ver.get('id', ''),
                sequence_number=ver.get('sequence_number', ver.get('sequenceNumber', 0)),
                description=ver.get('description', ''),
                model_name=ver.get('model_name', ver.get('modelName', '')),
                model_provider=ver.get('model_provider', ver.get('modelProvider', '')),
                temperature=temperature,
                template_format=ver.get('template_format', ver.get('templateFormat', 'MUSTACHE')),
                messages=messages,
            )
        # Fallback to GraphQL list + get_version
        prompts = self.list_prompts()
        for p in prompts:
            if p.name == prompt_name and p.versions:
                latest = max(p.versions, key=lambda v: v.sequence_number)
                return self.get_version(latest.id)
        raise ValueError(f"Prompt not found: {prompt_name}")

    def get_prompt_version(self, prompt_name: str, seq: int) -> PromptVersion:
        """Get a specific version of a prompt by name and sequence number."""
        prompts = self.list_prompts()
        for p in prompts:
            if p.name == prompt_name:
                for v in p.versions:
                    if v.sequence_number == seq:
                        return self.get_version(v.id)
                raise ValueError(f"Version {seq} not found for {prompt_name}")
        raise ValueError(f"Prompt not found: {prompt_name}")

    def deploy_version(self, prompt_name: str, template_text: str,
                       description: str = '', model_name: str = 'gpt-5.1',
                       model_provider: str = 'OPENAI',
                       temperature: float = 0.5) -> dict:
        """Deploy a new prompt version via REST API."""
        payload = {
            'prompt': {'name': prompt_name},
            'version': {
                'description': description,
                'template_type': 'CHAT',
                'template_format': 'MUSTACHE',
                'template': {
                    'type': 'chat',
                    'messages': [{'role': 'system', 'content': template_text}],
                },
                'model_provider': model_provider,
                'model_name': model_name,
                'invocation_parameters': {
                    'type': 'openai',
                    'openai': {'temperature': temperature, 'top_p': 1.0},
                },
            },
        }
        resp = self._client.post(
            f'{self.url}/v1/prompts',
            json=payload,
            headers={'Content-Type': 'application/json'},
        )
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Deploy failed (HTTP {resp.status_code}): {resp.text[:300]}")
        return resp.json().get('data', {})
