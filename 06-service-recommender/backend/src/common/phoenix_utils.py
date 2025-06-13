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

logger = logging.getLogger(__name__)


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


def configure_phoenix(only_if_alive=True):
    "Set only_if_alive=False to fail fast if Phoenix is not reachable."
    if only_if_alive and not service_alive():
        return

    if opentelemetry.trace._TRACER_PROVIDER:
        logger.info("Opentelemetry tracing already configured; skipping")
        return

    # PHOENIX_COLLECTOR_ENDPOINT env variable is used by phoenix.otel
    endpoint = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
    logger.info("Using Phoenix endpoint: %s", endpoint)

    # Both implementations produce the same traces
    if USE_PHOENIX_OTEL_REGISTER:
        # Using Phoenix docs: https://arize.com/docs/phoenix/tracing/integrations-tracing/haystack
        logger.info("Using phoenix.otel.register")
        # This uses PHOENIX_COLLECTOR_ENDPOINT and PHOENIX_PROJECT_NAME env variables
        phoenix.otel.register(
            # Auto-instrument based on installed OpenInference dependencies
            auto_instrument=True,
        )
    else:
        # Using Haystack docs: https://haystack.deepset.ai/integrations/arize-phoenix
        logger.info("Using HaystackInstrumentor")
        tracer_provider = otel_sdk_trace.TracerProvider()
        tracer_provider.add_span_processor(
            otel_sdk_trace.export.SimpleSpanProcessor(
                otel_trace_exporter.OTLPSpanExporter(f"{endpoint}/v1/traces")
            )
        )
        HaystackInstrumentor().instrument(tracer_provider=tracer_provider)


def get_prompt_template(prompt_name):
    # Get the template from Phoenix
    client = create_client()
    # # Pull a prompt by name
    prompt = client.prompts.get(prompt_identifier=prompt_name, tag="staging")
    # prompt = client.prompts.get(prompt_version_id="UHJvbXB0VmVyc2lvbjox")
    prompt_data = prompt._dumps()
    logger.info("prompt: %s", pformat(prompt_data))
    # pprint(prompt_data['template'].get('messages', None))
    return prompt
