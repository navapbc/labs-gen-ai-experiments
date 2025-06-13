import logging
from pprint import pformat

from hayhooks import BasePipelineWrapper
from haystack import Document, Pipeline
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.dataclasses import ChatMessage
from haystack.document_stores.in_memory import InMemoryDocumentStore

# https://github.com/deepset-ai/hayhooks?tab=readme-ov-file#sharing-code-between-pipeline-wrappers
from common import haystack_utils, phoenix_utils

logger = logging.getLogger(f"my_hayhook.{__name__}")


class OpenAiRagPipeline(BasePipelineWrapper):
    def setup(self) -> None:
        logger.info("Setting up %s", self.__class__.__name__)
        haystack_utils.set_up_tracing(logger.name)
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

    # TODO: stream response https://docs.haystack.deepset.ai/docs/hayhooks#streaming-responses

    def run_api(self, question: str) -> str:
        results = self.pipeline.run(
            {
                "retriever": {"query": question},
                "prompt_builder": {"question": question},
            }
        )
        logger.info("Results: %s", pformat(results))

        print(results)
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
