import os
import logging
from pprint import pprint

# https://docs.arize.com/phoenix/tracing/integrations-tracing/haystack
# pip install arize-phoenix-otel openinference-instrumentation-haystack haystack-ai
import phoenix.otel

# https://github.com/deepset-ai/hayhooks?tab=readme-ov-file#sharing-code-between-pipeline-wrappers
# Must use Option 3 https://github.com/deepset-ai/hayhooks/tree/main/examples/shared_code_between_wrappers#option-3-launch-hayhooks-with-the---additional-python-path-flag
import hs_utils
from dotenv import load_dotenv
from haystack import Pipeline, tracing
from haystack.tracing.logging_tracer import LoggingTracer
from openinference.instrumentation.haystack import HaystackInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
import opentelemetry.sdk.trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
logger = logging.getLogger(f"haystack.{__name__}")


def configure_phoenix():
    endpoint = os.environ.get("COLLECTOR_ENDPOINT", "http://localhost:6006")
    logger.info("Using Phoenix endpoint: %s", endpoint)

    # Both implementations produce the same traces
    if not True:
        logger.info("Haystack doc: Using OpenTelemetry Instrumentation for Haystack")
        # https://haystack.deepset.ai/integrations/arize-phoenix
        # Logs to default project
        endpoint_url = f"{endpoint}/v1/traces"  # The URL to your Phoenix instance
        tracer_provider = opentelemetry.sdk.trace.TracerProvider()
        tracer_provider.add_span_processor(
            SimpleSpanProcessor(OTLPSpanExporter(endpoint_url))
        )
        HaystackInstrumentor().instrument(tracer_provider=tracer_provider)
    else:
        logger.info("Phoenix doc: Using OpenInference Instrumentation for Haystack")
        # https://arize.com/docs/phoenix/tracing/integrations-tracing/haystack
        os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = endpoint
        # Creates project if it does not exist
        phoenix.otel.register(
            project_name="my-haystack-rag",
            auto_instrument=True,  # Auto-instrument your app based on installed OI dependencies
        )


# https://docs.haystack.deepset.ai/v2.8/docs/tracing#opentelemetry
# To add traces to even deeper levels of your pipelines, we recommend you check out OpenTelemetry integrations, such as:
# - urllib3 instrumentation for tracing HTTP requests in your pipeline,
# - OpenAI instrumentation for tracing OpenAI requests.


# https://docs.haystack.deepset.ai/docs/tracing#real-time-pipeline-logging
def setup_haystack_tracing():
    # https://docs.haystack.deepset.ai/v2.8/docs/tracing#content-tracing
    # By default, this behavior is disabled to prevent sensitive user information
    # from being sent to your tracing backend.
    # Or set the environment variable HAYSTACK_CONTENT_TRACING_ENABLED to true
    tracing.tracer.is_content_tracing_enabled = True
    # Add color tags to highlight each component's name and input
    tracing.enable_tracing(
        LoggingTracer(
            tags_color_strings={
                "haystack.component.input": "\x1b[1;31m",
                "haystack.component.name": "\x1b[1;34m",
            }
        )
    )


if __name__ == "__main__":
    logging.basicConfig(
        format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO
    )
    logging.getLogger("haystack").setLevel(logging.DEBUG)
    load_dotenv()

    configure_phoenix()

    pipeline = Pipeline()

    # setup_haystack_tracing()  # independent of Phoenix

    retriever = hs_utils.create_retriever(hs_utils.create_in_memory_doc_store())
    pipeline.add_component("retriever", retriever)

    if True:
        # connect_to_openai uses ChatPromptBuilder
        hs_utils.connect_to_openai(pipeline)
    # else:
    #     if False:
    #         # connect_to_amazon uses PromptBuilder
    #         hs_utils.connect_to_amazon(pipeline)
    #     else:
    #         hs_utils.connect_to_amazon_using_chat_prompt_builder(pipeline)

    logger.info("Pipeline %s", pipeline)

    # Ask a question
    question = "Who lives in Paris?"
    results = pipeline.run(
        {
            "retriever": {"query": question},
            "prompt_builder": {"question": question},
        }
    )

    pprint(results)
    replies = results.get("llm", {}).get("replies", [])
    if not replies:
        logger.warning("No replies found in the results.")
    else:
        logger.info("Replies: %s", replies)
        if hasattr(replies[0], "text"):
            print(replies[0].text)
        else:
            print(replies[0])

    if False:
        pprint(retriever)
        # run() any component directly
        retriever_out = retriever.run(query=question)

        pipeline.show()
