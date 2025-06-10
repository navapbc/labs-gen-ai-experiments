import os
import logging
from haystack import Document, Pipeline
from haystack.components.builders import PromptBuilder
from haystack.components.builders.chat_prompt_builder import ChatPromptBuilder
from haystack.components.converters import OutputAdapter
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.dataclasses import ChatMessage
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.utils import Secret

# https://docs.arize.com/phoenix/tracing/integrations-tracing/haystack
# pip install arize-phoenix-otel openinference-instrumentation-haystack haystack-ai
import phoenix.otel

from openinference.instrumentation.haystack import HaystackInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
import opentelemetry.sdk.trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

logger = logging.getLogger(f"haystack.{__name__}")

def configure_phoenix(project_name):
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
            project_name=project_name,
            auto_instrument=True,  # Auto-instrument your app based on installed OI dependencies
        )

def create_in_memory_doc_store():
    # Write documents to InMemoryDocumentStore
    document_store = InMemoryDocumentStore()
    document_store.write_documents(
        [
            Document(content="My name is Jean and I live in Paris."),
            Document(content="My name is Mark and I live in Berlin."),
            Document(content="My name is Giorgio and I live in Rome."),
        ]
    )
    return document_store


def create_retriever(document_store: InMemoryDocumentStore):
    return InMemoryBM25Retriever(document_store=document_store)

from pprint import pprint
from  phoenix.client import Client
# TODO: Use environment variables
phoenix_base_url = None # defaults to "http://localhost:6006"

def create_chat_template():
    # Get the template from Phoenix
    # TODO: connect using API key -- https://arize.com/docs/phoenix/sdk-api-reference/python-pacakges/arize-phoenix-client#authentication-if-applicable
    client = Client(base_url=phoenix_base_url) # endpoint="https://my-phoenix.com"
    # # Pull a prompt by name
    prompt_name = "teacher"
    prompt = client.prompts.get(prompt_identifier=prompt_name, tag="staging")
    # prompt = Client().prompts.get(prompt_version_id="UHJvbXB0VmVyc2lvbjox")
    print("prompt")
    prompt_data = prompt._dumps()
    pprint(prompt_data)
    # pprint(prompt_data['template'].get('messages', None))

    # # Can format for openai, anthropic, and google_generativeai
    formatted_prompt = prompt.format(variables={"grade_level": "middle-school", "question": "What is RAG for AI?"})
    print("formatted_prompt")
    pprint(formatted_prompt)

    return [
        ChatMessage.from_system("You are a helpful assistant."),
        ChatMessage.from_user(
            "Given these documents, answer the question.\n"
            "Documents:\n{% for doc in documents %}{{ doc.content }}{% endfor %}\n"
            "Question: {{question}}\n"
            "Answer:"
        ),
    ]


def create_llm_openai():
    return OpenAIChatGenerator(api_key=Secret.from_env_var("OPENAI_API_KEY"))


def connect_to_openai(rag_pipeline: Pipeline):
    llm = create_llm_openai()
    rag_pipeline.add_component("llm", llm)

    template = create_chat_template()
    # Define required variables explicitly
    prompt_builder = ChatPromptBuilder(
        template=template, required_variables=["question", "documents"]
    )
    # Alternatively, you can use a wildcard to include all variables:
    # prompt_builder = ChatPromptBuilder(template=template, required_variables="*")

    rag_pipeline.add_component("prompt_builder", prompt_builder)
    rag_pipeline.connect("retriever.documents", "prompt_builder.documents")
    rag_pipeline.connect("prompt_builder.prompt", "llm.messages")

