from __future__ import annotations

"""Base class for trace adapters."""
from abc import ABC, abstractmethod


class TraceAdapter(ABC):
    """Abstract base class for extracting structured data from trace spans.

    Each LLM system has different span structures. Write an adapter to
    map your system's spans to the standard trace format.
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @abstractmethod
    def get_prompt_type(self, spans: list[dict]) -> str | None:
        """Determine the prompt/task type from spans. Return None to skip."""
        ...

    @abstractmethod
    def get_user_query(self, spans: list[dict]) -> str:
        """Extract the user's query text."""
        ...

    @abstractmethod
    def get_output(self, spans: list[dict]) -> tuple[str, dict | None]:
        """Extract the LLM output.

        Returns:
            Tuple of (raw_output_string, parsed_json_or_none).
        """
        ...

    @abstractmethod
    def get_resources(self, parsed_output: dict) -> list[dict]:
        """Extract resources list from parsed output."""
        ...

    def get_context(self, spans: list[dict]) -> str:
        """Extract RAG/retrieval context. Override if your system uses RAG."""
        return ''

    def get_metadata(self, spans: list[dict]) -> dict:
        """Extract additional metadata (timestamp, location, email, etc.)."""
        return {}
