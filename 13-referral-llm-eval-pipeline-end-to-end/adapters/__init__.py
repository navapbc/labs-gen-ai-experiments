from __future__ import annotations

from adapters.base import TraceAdapter
from adapters.referral_adapter import ReferralAdapter
from adapters.generic_adapter import GenericAdapter

ADAPTER_REGISTRY = {
    'referral': ReferralAdapter,
    'generic': GenericAdapter,
}


def get_adapter(name: str, config: dict | None = None) -> TraceAdapter:
    """Get adapter by name."""
    cls = ADAPTER_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown adapter: {name}. Available: {list(ADAPTER_REGISTRY.keys())}")
    return cls(config=config or {})
