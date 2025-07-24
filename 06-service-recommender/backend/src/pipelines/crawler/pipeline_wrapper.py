import logging
from pprint import pformat

import hayhooks

# https://github.com/deepset-ai/hayhooks?tab=readme-ov-file#sharing-code-between-pipeline-wrappers
from common import haystack_utils, phoenix_utils
from hayhooks import BasePipelineWrapper
from haystack import Document, Pipeline
from haystack.components.builders.chat_prompt_builder import ChatPromptBuilder
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.dataclasses.chat_message import ChatMessage
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack_integrations.components.generators.amazon_bedrock import (
    AmazonBedrockChatGenerator,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO
)


class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        logger.info("Setting up %s", self.__class__.__name__)

        phoenix_utils.configure_phoenix()
        self.pipeline = self._create_pipeline()

    def _create_pipeline(self) -> Pipeline:
        pipeline = Pipeline()
        llm = self._create_llm_chat_generator()
        pipeline.add_component("llm", llm)

        chat_template = [
            ChatMessage.from_system(
                "You are a helpful assistant that scrapes a user-specified website and provides structured JSON output about the described service.\n"
                "The JSON output should include:\n"
                "- 'name': name of the service\n"
                "- 'type': what kind of service it is or the service or resource it is providing\n"
                "- 'eligibility': who is eligible for the services\n"
                "- 'service_area': the geographic area served by the service\n"
                "\n"
                "If the website does not provide certain information about the service, set the corresponding field to null.\n"
            ),
            ChatMessage.from_user("The website URL is {{url}}. "),
        ]

        # Use a wildcard to include all required variables mentioned in the template
        prompt_builder = ChatPromptBuilder(
            template=chat_template, required_variables="*"
        )
        pipeline.add_component("prompt_builder", prompt_builder)

        pipeline.connect("prompt_builder.prompt", "llm.messages")

        logger.info("Pipeline %s", pipeline)
        return pipeline

    def _create_llm_chat_generator(self):
        # NOTE: The LLMs tested do not actually scrape the website
        if True:
            return OpenAIChatGenerator(model="gpt-4o")
        else:
            return AmazonBedrockChatGenerator(model="us.anthropic.claude-3-7-sonnet-20250219-v1:0")

    # Called for the `{pipeline_name}/run` endpoint
    def run_api(self, url: str) -> str:
        results = self.pipeline.run(
            {
                "prompt_builder": {"url": url},
            }
        )
        logger.info("Results: %s", pformat(results))
        replies = results.get("llm", {}).get("replies", [])
        if not replies:
            logger.warning("No replies found in the results.")
            return "No replies found."
        else:
            logger.info("Replies: %s", replies)
            if hasattr(replies[0], "text"):
                return replies[0].text
            else:
                return replies[0]

    # https://docs.haystack.deepset.ai/docs/hayhooks#openai-compatibility
    # Called for the `{pipeline_name}/chat`, `/chat/completions`, or `/v1/chat/completions` streaming endpoint using Server-Sent Events (SSE)
    def run_chat_completion(self, model: str, messages: list, body: dict):
        logger.info(
            "Running chat completion with model: %s, messages: %s", model, messages
        )
        url = hayhooks.get_last_user_message(messages)
        logger.info("URL: %s", url)
        # stream response https://docs.haystack.deepset.ai/docs/hayhooks#streaming-responses
        # https://github.com/deepset-ai/hayhooks?tab=readme-ov-file#streaming-responses-in-openai-compatible-endpoints
        return hayhooks.streaming_generator(
            pipeline=self.pipeline,
            pipeline_run_args={
                "prompt_builder": {"url": url},
            },
        )
