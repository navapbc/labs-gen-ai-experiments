import json
from typing import Optional, List, Any, Dict

from opentelemetry.sdk.trace import SpanProcessor, ReadableSpan, Event, Span
from opentelemetry.sdk.trace.export import SpanExporter
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


class PresidioRedactionSpanProcessor(SpanProcessor):
    """
    OpenTelemetry span processor that redacts PII data using Microsoft Presidio.
    """

    def __init__(
            self,
            exporter: SpanExporter,
            entities: Optional[List[str]] = None,
            language: str = "en"
    ):
        """
        Initialize the PII redacting processor with Presidio and an exporter.

        Args:
            exporter: The span exporter to use after PII redaction
            entities: List of PII entity types to detect and redact.
                     If None, uses a default set of common PII types.
            language: Language to use for NLP analysis
        """
        self._exporter = exporter

        # Default supported entity types in Presidio
        self._default_entities = [
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN",
            "CREDIT_CARD", "IP_ADDRESS", "DATE_TIME", "US_BANK_NUMBER",
            "US_DRIVER_LICENSE", "LOCATION", "NRP", "US_PASSPORT",
            "US_ITIN", "CRYPTO", "UK_NHS", "IBAN_CODE"
        ]

        self._entities = entities or self._default_entities

        # Set up Presidio engines with proper configuration
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": language, "model_name": "en_core_web_lg"}
            ]
        }
        nlp_engine = NlpEngineProvider(nlp_configuration=nlp_configuration).create_engine()
        self._analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        self._anonymizer = AnonymizerEngine()

        # Default operator for anonymization (replacement with entity type)
        self._operators = {
            entity: OperatorConfig("replace", {"new_value": f"[REDACTED_{entity}]"})
            for entity in self._entities
        }

    def _redact_string(self, value: str) -> str:
        """Redact PII from any string value using Presidio."""
        if not value.strip():
            return value

        try:
            # Analyze the text for PII
            results = self._analyzer.analyze(
                text=value,
                entities=self._entities,
                language="en"
            )

            # If PII is found, anonymize it
            if results:
                anonymized_text = self._anonymizer.anonymize(
                    text=value,
                    analyzer_results=results,
                    operators=self._operators
                )
                return anonymized_text.text

            return value
        except Exception as e:
            print(f"Error redacting string: {str(e)}")
            return "[REDACTION_ERROR]"

    def _redact_value(self, value: Any) -> Any:
        """
        Redact PII from any value type.
        Handles strings, numbers, booleans, lists, and dictionaries.
        """
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
        """
        redacted_attributes = {}

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
        # Create redacted attributes
        redacted_attributes = self._redact_span_attributes(span)

        # Redact span name
        redacted_name = self._redact_string(span.name)

        # Handle events
        redacted_events = []
        for event in span.events:
            redacted_event_attrs = {
                k: self._redact_value(v) for k, v in event.attributes.items()
            }
            # Create new event with redacted attributes
            redacted_event = Event(
                name=self._redact_string(event.name),
                attributes=redacted_event_attrs,
                timestamp=event.timestamp
            )
            redacted_events.append(redacted_event)

        # Create new span with redacted data
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
            instrumentation_scope=span.instrumentation_scope
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