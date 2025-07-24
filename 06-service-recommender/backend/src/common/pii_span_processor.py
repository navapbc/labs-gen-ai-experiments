import logging
import re
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import SpanExporter
import json
from typing import Any, Dict, Optional
from opentelemetry.trace import Span
from opentelemetry.sdk.trace import ReadableSpan


logger = logging.getLogger(__name__)

class PIIRedactingSpanProcessor(SpanProcessor):
    def __init__(self, exporter: SpanExporter, pii_patterns: Optional[Dict[str, str]] = None):
        """
        Initialize the PII redacting processor with an exporter and optional patterns.

        Args:
            exporter: The span exporter to use after PII redaction
            pii_patterns: Dictionary of pattern names and their regex patterns
        """
        logger.error("PII FIlTER INIT called") # todo mrh remove
        self._exporter = exporter
        self._default_patterns = {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'date_of_birth': r'\b\d{2}[-/]\d{2}[-/]\d{4}\b',
        }
        self._patterns = {**self._default_patterns, **(pii_patterns or {})}

        # Compile patterns for better performance
        self._compiled_patterns = {
            name: re.compile(pattern) for name, pattern in self._patterns.items()
        }

    def _redact_string(self, value: str) -> str:
        """Redact PII from any string value."""
        logger.error("PII FIlTER redact string called") # todo mrh remove
        redacted = value
        for pattern_name, pattern in self._compiled_patterns.items():
            redacted = pattern.sub(f'[REDACTED_{pattern_name.upper()}]', redacted)
        return redacted

    def _redact_value(self, value: Any) -> Any:
        """
        Redact PII from any value type.
        Handles strings, numbers, booleans, lists, and dictionaries.
        """
        logger.error("PII FIlTER redactvalue called") # todo mrh remove
        if isinstance(value, str):
            try:
                # Try to parse as JSON first
                json_obj = json.loads(value)
                return json.dumps(self._redact_value(json_obj))
            except json.JSONDecodeError:
                # If not valid JSON, treat as regular string
                return self._redact_string(value)
        elif isinstance(value, dict):
            return {k: self._redact_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._redact_value(item) for item in value]
        elif isinstance(value, (int, float, bool, type(None))):
            return value
        else:
            # Convert any other types to string and redact
            return self._redact_string(str(value))

    def _redact_span_attributes(self, span: ReadableSpan) -> Dict[str, Any]:
        """
        Create a new dictionary of redacted span attributes.
        Returns the redacted attributes instead of modifying in place.
        """
        redacted_attributes = {}
        logger.error("PII FIlTER redact span attributes called") # todo mrh remove
        for key, value in span.attributes.items():
            # Skip certain metadata attributes that shouldn't contain PII
            if key in {'service.name', 'telemetry.sdk.name', 'telemetry.sdk.version'}:
                redacted_attributes[key] = value
                continue

            try:
                redacted_value = self._redact_value(value)
                redacted_attributes[key] = redacted_value
            except Exception as e:
                redacted_attributes[key] = "[REDACTION_ERROR]"
                print(f"Error redacting attribute {key}: {str(e)}")

        return redacted_attributes

    def _create_redacted_span(self, span: ReadableSpan) -> ReadableSpan:
        """
        Create a new span with redacted attributes instead of modifying the original.
        """
        logger.error("PII FIlTER create redacted span called") # todo mrh remove
        # Create redacted attributes
        redacted_attributes = self._redact_span_attributes(span)

        # Create a new span with redacted name and attributes
        redacted_name = self._redact_string(span.name)

        # Handle events
        redacted_events = []
        for event in span.events:
            redacted_event_attrs = {
                k: self._redact_value(v) for k, v in event.attributes.items()
            }
            # Create new event with redacted attributes
            from opentelemetry.sdk.trace import Event
            redacted_event = Event(
                name=self._redact_string(event.name),
                attributes=redacted_event_attrs,
                timestamp=event.timestamp
            )
            redacted_events.append(redacted_event)

        logger.error(f"Michelle: the redacted_attributes are {redacted_attributes}") # TODO MRH remove
        # Create new span with redacted data
        from opentelemetry.sdk.trace import Span
        redacted_span = ReadableSpan(
            name=redacted_name,
            context=span.get_span_context(),
            parent=span.parent,
            resource=span.resource,
            attributes=redacted_attributes,
            events=redacted_events,
            links=span.links,
            kind=span.kind,
            status=span.status,
            start_time=span.start_time,
            end_time=span.end_time,
            instrumentation_info=span.instrumentation_info
        )

        return redacted_span

    def on_start(self, span: Span, parent_context: Optional[Any] = None):
        """Called when a span starts."""
        pass

    def on_end(self, span: ReadableSpan):
        """Called when a span ends. Creates a redacted copy and exports it."""
        redacted_span = self._create_redacted_span(span)
        self._exporter.export([redacted_span])

    def shutdown(self):
        """Shuts down the processor and exporter."""
        self._exporter.shutdown()

    def force_flush(self, timeout_millis: int = 30000):
        """Forces flush of pending spans."""
        self._exporter.force_flush(timeout_millis)