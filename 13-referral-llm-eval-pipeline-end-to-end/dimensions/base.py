from __future__ import annotations

"""Base class and result type for evaluation dimensions."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class DimensionResult:
    """Result from evaluating a single dimension."""
    flags: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)


class EvalDimension(ABC):
    """Abstract base class for evaluation dimensions."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this dimension."""
        ...

    @abstractmethod
    def evaluate(self, resources: list[dict], context: dict) -> DimensionResult:
        """Evaluate resources on this dimension.

        Args:
            resources: List of resource dicts from parsed output.
            context: Dict with keys like 'user_query', 'location',
                     'resources_context', 'raw_content', 'parsed_json'.

        Returns:
            DimensionResult with flags and details.
        """
        ...
