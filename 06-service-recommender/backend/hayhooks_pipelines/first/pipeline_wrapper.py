from pprint import pformat
from haystack import Pipeline
from hayhooks import BasePipelineWrapper

import logging
from haystack import tracing
from haystack.tracing.logging_tracer import LoggingTracer

# https://github.com/deepset-ai/hayhooks?tab=readme-ov-file#sharing-code-between-pipeline-wrappers
# Must use Option 3 https://github.com/deepset-ai/hayhooks/tree/main/examples/shared_code_between_wrappers#option-3-launch-hayhooks-with-the---additional-python-path-flag
from common import hs_utils

logger = logging.getLogger(f"my_hayhook.{__name__}")


# https://docs.haystack.deepset.ai/docs/tracing#real-time-pipeline-logging
def setup_tracing():
    logging.basicConfig(
        format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING
    )
    logging.getLogger("haystack").setLevel(logging.DEBUG)
    logging.getLogger("my_hayhook").setLevel(logging.DEBUG)

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
                "my_hayhook": "\x1b[1;34m",
            }
        )
    )
# setup_tracing()

class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        logger.info("Setting up the PipelineWrapper...")
        hs_utils.configure_phoenix("my-hayhooks-rag")
        self.pipeline = self._create_pipeline()

    def _create_pipeline(self) -> Pipeline:
        pipeline = Pipeline()
        retriever = hs_utils.create_retriever(hs_utils.create_in_memory_doc_store())
        pipeline.add_component("retriever", retriever)

        hs_utils.connect_to_openai(pipeline)
        # else:
        #     if False:
        #         # connect_to_amazon uses PromptBuilder
        #         hs_utils.connect_to_amazon(pipeline)
        #     else:
        #         hs_utils.connect_to_amazon_using_chat_prompt_builder(pipeline)
        logger.info("Pipeline %s", pipeline)
        return pipeline

    # TODO: https://docs.haystack.deepset.ai/docs/hayhooks#streaming-responses

    def run_api(self, question: str) -> str:
        # result = self.pipeline.run({"input": {"text": input_text}})
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
