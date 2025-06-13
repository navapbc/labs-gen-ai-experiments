import logging

from haystack import Pipeline, tracing
from haystack.components.builders.chat_prompt_builder import ChatPromptBuilder
from haystack.dataclasses.chat_message import ChatMessage
from haystack.tracing.logging_tracer import LoggingTracer

from phoenix.client.types.prompts import PromptVersion

logger = logging.getLogger(f"haystack.{__name__}")


# https://docs.haystack.deepset.ai/docs/tracing#real-time-pipeline-logging
def set_up_tracing(logger_name: str):
    # logging.basicConfig(
    #     format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING
    # )
    logging.getLogger("haystack").setLevel(logging.DEBUG)

    # TODO: Determine when to enable content tracing
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
                logger_name: "\x1b[1;34m",
            }
        )
    )


def create_rag_pipeline(retriever, llm, prompt_version: PromptVersion) -> Pipeline:
    rag_pipeline = Pipeline()
    rag_pipeline.add_component("retriever", retriever)

    rag_pipeline.add_component("llm", llm)

    chat_template = to_chat_messages(prompt_version)
    # Use a wildcard to include all required variables mentioned in the template
    prompt_builder = ChatPromptBuilder(template=chat_template, required_variables="*")

    rag_pipeline.add_component("prompt_builder", prompt_builder)
    rag_pipeline.connect("retriever.documents", "prompt_builder.documents")
    rag_pipeline.connect("prompt_builder.prompt", "llm.messages")
    return rag_pipeline


def to_chat_messages(prompt_version: PromptVersion) -> list[ChatMessage]:
    messages = []
    for msg in prompt_version._template["messages"]:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            assert isinstance(content, str), f"Expected string, got {type(content)}"
            chat_msg = ChatMessage.from_system(content)
        elif role == "user":
            assert isinstance(content, str), f"Expected string, got {type(content)}"
            chat_msg = ChatMessage.from_user(content)
        else:
            raise ValueError(f"Unexpected role: {role} for message {msg}")
        messages.append(chat_msg)

    return messages
