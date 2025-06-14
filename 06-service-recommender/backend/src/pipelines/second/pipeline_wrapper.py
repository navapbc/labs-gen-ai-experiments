import logging

from haystack_integrations.components.generators.amazon_bedrock import (
    AmazonBedrockChatGenerator,
)

from pipelines.first.pipeline_wrapper import PipelineWrapper as FirstPipelineWrapper

logger = logging.getLogger(__name__)


class PipelineWrapper(FirstPipelineWrapper):
    def _create_llm_chat_generator(self, prompt_version):
        logger.warning(
            "Ignoring LLM model from prompt_template: %s %r",
            prompt_version._model_provider,
            prompt_version._model_name,
        )
        bedrock_model = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        return AmazonBedrockChatGenerator(model=bedrock_model)
