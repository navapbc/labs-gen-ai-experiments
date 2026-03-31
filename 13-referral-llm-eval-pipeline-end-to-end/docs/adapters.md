# Writing Custom Adapters

Adapters tell the pipeline how to extract structured data from your LLM system's trace spans.

## The TraceAdapter Interface

```python
from adapters.base import TraceAdapter

class MyAdapter(TraceAdapter):
    def get_prompt_type(self, spans: list[dict]) -> str | None:
        """Return task type string, or None to skip this trace."""
        ...

    def get_user_query(self, spans: list[dict]) -> str:
        """Return the user's query text."""
        ...

    def get_output(self, spans: list[dict]) -> tuple[str, dict | None]:
        """Return (raw_output, parsed_json_or_none)."""
        ...

    def get_resources(self, parsed_output: dict) -> list[dict]:
        """Return list of resource dicts from parsed output."""
        ...

    # Optional overrides:
    def get_context(self, spans: list[dict]) -> str:
        """Return RAG/retrieval context for grounding checks."""
        return ''

    def get_metadata(self, spans: list[dict]) -> dict:
        """Return extra metadata (timestamp, location, email, etc.)."""
        return {}
```

## Span Structure

Each span is a dict with at minimum:
- `name`: The span name (e.g., `"ChatCompletion"`, `"MyPipeline.run"`)
- `attributes`: Dict (or JSON string) of span attributes
- `start_time`: ISO timestamp
- `context`: Dict with `trace_id`

Attributes commonly include:
- `input.value`: The input to this span
- `output.value`: The output from this span
- `user.id`: User identifier

## Example: Referral System

```python
class ReferralAdapter(TraceAdapter):
    PROMPT_TYPES = {
        'generate_referrals_rag--centraltx': 'referraltx',
        'generate_action_plan': 'actionplan',
    }

    def get_prompt_type(self, spans):
        for span in spans:
            if span['name'] in self.PROMPT_TYPES:
                return self.PROMPT_TYPES[span['name']]
        return None

    def get_output(self, spans):
        for span in spans:
            if span['name'] == 'ReadableLogger.run':
                raw = parse_attributes(span['attributes']).get('output.value', '')
                try:
                    return raw, json.loads(raw)
                except json.JSONDecodeError:
                    return raw, None
        return '', None
```

## Registering Your Adapter

Add it to `adapters/__init__.py`:

```python
from adapters.my_adapter import MyAdapter

ADAPTER_REGISTRY = {
    'referral': ReferralAdapter,
    'generic': GenericAdapter,
    'my_system': MyAdapter,  # Add here
}
```

Then reference it in your config:

```yaml
extraction:
  adapter: my_system
```

## Tips

- **Start with GenericAdapter** to see what data you get, then write a custom one
- **Return None from `get_prompt_type`** to skip traces you don't care about (e.g., internal health checks)
- **Use `parse_attributes()`** from `lib/trace_parser.py` to safely handle string-or-dict attributes
- **The `get_resources` method** should return a list of dicts, ideally with keys like `name`, `addresses`, `phones`, `website`, `description`
