import logging
import os
from pprint import pformat

import httpx

# OpenTelemetry is a common standard for general observability
import opentelemetry.exporter.otlp.proto.http.trace_exporter as otel_trace_exporter
import opentelemetry.sdk.trace as otel_sdk_trace
import opentelemetry.trace

# https://docs.arize.com/phoenix/tracing/integrations-tracing/haystack
# Arize's Phoenix observability platform
import phoenix.client
import phoenix.otel

# Arize's OpenInference is a set of conventions that is complimentary to OpenTelemetry
from openinference.instrumentation.haystack import HaystackInstrumentor

from common.app_config import config
from common.presidio_pii_filter import PresidioRedactionSpanProcessor

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s")


def create_client():
    return phoenix.client.Client(base_url=config.phoenix_base_url)


def service_alive():
    client = create_client()
    try:
        client.projects.list()
        return True
    except httpx.HTTPStatusError as error:
        logger.info("Phoenix service is not alive: %s", error)
    return False


USE_PHOENIX_OTEL_REGISTER = True
BATCH_OTEL = True


def configure_phoenix(only_if_alive=True):
    "Set only_if_alive=False to fail fast if Phoenix is not reachable."
    if only_if_alive and not service_alive():
        return

    if opentelemetry.trace._TRACER_PROVIDER:
        logger.info("Opentelemetry tracing already configured; skipping")
        return

    # PHOENIX_COLLECTOR_ENDPOINT env variable is used by phoenix.otel
    endpoint = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
    trace_endpoint = f"{endpoint}/v1/traces"
    logger.info("Using Phoenix endpoint: %s", endpoint)

    # Both implementations produce the same traces
    if USE_PHOENIX_OTEL_REGISTER:
        # Using Phoenix docs: https://arize.com/docs/phoenix/tracing/integrations-tracing/haystack
        logger.info("Using phoenix.otel.register")
        # This uses PHOENIX_COLLECTOR_ENDPOINT and PHOENIX_PROJECT_NAME env variables
        # and PHOENIX_API_KEY to handle authentication to Phoenix.
        tracer_provider = phoenix.otel.register(
            batch=BATCH_OTEL,
            # Auto-instrument based on installed OpenInference dependencies
            auto_instrument=True,
        )
        span_exporter = otel_trace_exporter.OTLPSpanExporter(trace_endpoint)
        otel_sdk_trace.export.BatchSpanProcessor(span_exporter)
        # Create the PII redacting processor with the OTLP exporter
        pii_processor = PresidioRedactionSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(pii_processor)
    else:
        # Using Haystack docs: https://haystack.deepset.ai/integrations/arize-phoenix
        # This is a more manual setup that uses HaystackInstrumentor
        # Since this doesn't use PHOENIX_PROJECT_NAME, it logs to the 'default' Phoenix project
        logger.info("Using HaystackInstrumentor")
        tracer_provider = otel_sdk_trace.TracerProvider()
        # Set the URL since PHOENIX_COLLECTOR_ENDPOINT is not used by HaystackInstrumentor
        span_exporter = otel_trace_exporter.OTLPSpanExporter(f"{endpoint}/v1/traces")
        if BATCH_OTEL:
            processor = otel_sdk_trace.export.BatchSpanProcessor(span_exporter)
        else:
            # Send traces immediately
            processor = otel_sdk_trace.export.SimpleSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(processor)
        # Create the PII redacting processor with the OTLP exporter
        pii_processor = PresidioRedactionSpanProcessor(
            otel_trace_exporter.OTLPSpanExporter(trace_endpoint),
        )
        tracer_provider.add_span_processor(pii_processor)
        # PHOENIX_API_KEY env variable seems to be used by HaystackInstrumentor
        HaystackInstrumentor().instrument(tracer_provider=tracer_provider)


def get_prompt_template(prompt_name):
    # Get the template from Phoenix
    client = create_client()
    # Pull a prompt by name
    prompt = client.prompts.get(prompt_identifier=prompt_name, tag="staging")
    prompt_data = prompt._dumps()
    logger.info("Retrieved prompt: %s", pformat(prompt_data))
    return prompt
