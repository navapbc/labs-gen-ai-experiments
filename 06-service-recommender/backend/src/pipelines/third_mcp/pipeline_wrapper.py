import logging
from pprint import pformat

# https://github.com/deepset-ai/hayhooks?tab=readme-ov-file#sharing-code-between-pipeline-wrappers
from common import phoenix_utils
from hayhooks import BasePipelineWrapper
from haystack import Pipeline
from haystack.components.converters import OutputAdapter
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.tools import ToolInvoker
from haystack.dataclasses import ChatMessage
from haystack_integrations.tools.mcp import (
    MCPToolset,
    StreamableHttpServerInfo,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO
)


class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        logger.info("Setting up %s", self.__class__.__name__)

        phoenix_utils.configure_phoenix()
        self.pipeline = create_pipeline()

    # Called for the `{pipeline_name}/run` endpoint
    def run_api(self, question: str) -> str:
        user_input = ChatMessage.from_user(
            text=question
        )  # "What is the time in New York?")
        result = self.pipeline.run(
            {
                "llm": {"messages": [user_input]},
                "adapter": {"initial_msg": [user_input]},
            }
        )

        print(result["response_llm"]["replies"][0].text)
        logger.info("Result: %s", pformat(result))
        if not result:
            logger.warning("No result found.")
            return "No result found."
        else:
            logger.info("Result: %s", result)
            return str(result)


# For testing purposes, we can set this to True to only invoke the tool without generating a final response from the LLM
ONLY_INVOKE_TOOL = False


def create_pipeline(toolset=None) -> Pipeline:
    # https://docs.haystack.deepset.ai/docs/mcptoolset#in-a-pipeline
    if toolset is None:
        server_info = StreamableHttpServerInfo(url="http://127.0.0.1:8000/mcp")
        toolset = MCPToolset(server_info=server_info)

    pipeline = Pipeline()
    pipeline.add_component(
        "llm", OpenAIChatGenerator(model="gpt-4o-mini", tools=toolset)
    )
    pipeline.add_component("tool_invoker", ToolInvoker(tools=toolset))
    pipeline.connect("llm.replies", "tool_invoker.messages")

    if ONLY_INVOKE_TOOL:
        return pipeline

    pipeline.add_component(
        "adapter",
        OutputAdapter(
            template="{{ initial_msg + initial_tool_messages + tool_messages }}",
            output_type=list[ChatMessage],
            unsafe=True,
        ),
    )
    pipeline.add_component("response_llm", OpenAIChatGenerator(model="gpt-4o-mini"))

    pipeline.connect("llm.replies", "adapter.initial_tool_messages")
    pipeline.connect("tool_invoker.tool_messages", "adapter.tool_messages")
    pipeline.connect("adapter.output", "response_llm.messages")


def create_no_toolset_pipeline() -> Pipeline:
    pipeline = Pipeline()
    pipeline.add_component("llm", OpenAIChatGenerator(model="gpt-4o-mini", tools=None))
    return pipeline
