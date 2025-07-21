import logging
from pprint import pformat

import hayhooks
from hayhooks import BasePipelineWrapper
from haystack import Document, Pipeline
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.document_stores.in_memory import InMemoryDocumentStore

# https://github.com/deepset-ai/hayhooks?tab=readme-ov-file#sharing-code-between-pipeline-wrappers
from common import haystack_utils, phoenix_utils

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
        document_store = create_sample_in_memory_doc_store()
        retriever = InMemoryBM25Retriever(document_store=document_store)
        prompt_version = phoenix_utils.get_prompt_template("sample_rag")
        llm = self._create_llm_chat_generator(prompt_version)
        pipeline = haystack_utils.create_rag_pipeline(retriever, llm, prompt_version)
        logger.info("Pipeline %s", pipeline)
        return pipeline

    def _create_llm_chat_generator(self, prompt_version):
        return OpenAIChatGenerator()

    # Called for the `{pipeline_name}/run` endpoint
    def run_api(self, question: str) -> str:
        results = self.pipeline.run(
            {
                "retriever": {"query": question},
                "prompt_builder": {"question": question},
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
        question = hayhooks.get_last_user_message(messages)
        logger.info("Question: %s", question)
        # stream response https://docs.haystack.deepset.ai/docs/hayhooks#streaming-responses
        # https://github.com/deepset-ai/hayhooks?tab=readme-ov-file#streaming-responses-in-openai-compatible-endpoints
        return hayhooks.streaming_generator(
            pipeline=self.pipeline,
            pipeline_run_args={
                "retriever": {"query": question},
                "prompt_builder": {"question": question},
            },
        )


def create_sample_in_memory_doc_store():
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
