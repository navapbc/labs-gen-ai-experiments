import json
import logging
import os
from pathlib import Path
from pprint import pformat

from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage
from haystack_integrations.tools.mcp import (
    MCPTool,
    MCPToolset,
    StdioServerInfo,
    StreamableHttpServerInfo,
)
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.metadata_utils import get_display_name
from pipelines.third_mcp import pipeline_wrapper

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(levelname)s - %(name)s -  %(message)s", level=logging.INFO
)


def streamable():
    # Create an MCP tool that connects to an HTTP server
    server_info = StreamableHttpServerInfo(url="http://127.0.0.1:8000/mcp")
    tool = MCPTool(name="subtract", server_info=server_info)

    # Use the tool
    result = tool.invoke(a=7, b=3)
    logger.info("Result: %s", pformat(result))
    logger.info("JSON: %s", pformat(json.loads(result)))


def stdio():
    # Create an MCP tool that uses stdio transport
    server_info = StdioServerInfo(
        command="uvx", args=["mcp-server-time", "--local-timezone=America/Chicago"]
    )
    tool = MCPTool(name="get_current_time", server_info=server_info)

    # Get the current time in New York
    timezone = "America/New_York"
    timezone = "US/Mountain"
    result = tool.invoke(timezone=timezone)
    logger.info("Result: %s", pformat(result))
    logger.info("JSON: %s", pformat(json.loads(result)))


#


async def client():
    # Connect to a streamable HTTP server
    async with streamablehttp_client("http://127.0.0.1:8000/mcp") as (
        read_stream,
        write_stream,
        _,
    ):
        # Create a session using the client streams
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            await display_tools(session)
            await display_resources(session)
            # Call a tool
            # tool_result = await session.call_tool("echo", {"message": "hello"})


# https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#streamable-http-transport
async def display_tools(session: ClientSession):
    """Display available tools with human-readable names"""
    tools_response = await session.list_tools()
    logger.info("tools_response: %s", tools_response)

    for tool in tools_response.tools:
        # get_display_name() returns the title if available, otherwise the name
        display_name = get_display_name(tool)
        print(f"Tool: {display_name}")
        if tool.description:
            print(f"   {tool.description}")


async def display_resources(session: ClientSession):
    """Display available resources with human-readable names"""
    resources_response = await session.list_resources()
    logger.info("resources_response: %s", resources_response)

    for resource in resources_response.resources:
        display_name = get_display_name(resource)
        print(f"Resource: {display_name} ({resource.uri})")


def get_toolset():
    # https://docs.haystack.deepset.ai/docs/mcptoolset
    server_info = StreamableHttpServerInfo(url="http://127.0.0.1:8000/mcp")
    toolset = MCPToolset(
        server_info=server_info,
        tool_names=["Opportunity_Search"],  # Only include specific tools
    )

    logger.info("Resulting tools: %s", [t.name for t in toolset.tools])
    return toolset


#


def toolset_pipeline(question):
    toolset = get_toolset()
    # Haystack logs and Phoenix show `"tools": null` but tools are being passed to the
    # OpenAIChatGenerator llm when running the pipeline and it works :confused:

    # toolset = [t for t in toolset.tools if t.name in ["Health", "Opportunity_Search"]]
    # logger.info("Toolset: %s", [t.name for t in toolset.tools])

    pipeline = pipeline_wrapper.create_pipeline(toolset)
    if not os.path.exists("toolset_pipeline.png"):
        pipeline.draw(Path("toolset_pipeline.png"))

    user_input = ChatMessage.from_user(
        text=question
    )  # "What is the time in New York?")
    if pipeline_wrapper.ONLY_INVOKE_TOOL:
        result = pipeline.run(
            {
                "llm": {"messages": [user_input]},
            },
        )
    else:
        result = pipeline.run(
            {
                "llm": {"messages": [user_input]},
                "adapter": {"initial_msg": [user_input]},
            },
            include_outputs_from=["response_llm", "adapter", "llm", "tool_invoker"],
        )
        print(result["llm"]["replies"][0].text)
    logger.info("Result: %s", pformat(result))

    tool_result = json.loads(
        result["tool_invoker"]["tool_messages"][0].tool_call_result.result
    )
    result_content = json.loads(tool_result["content"][0]["text"])
    entity_list = result_content["data"]
    for entity in entity_list:
        print(f"Opportunity ID: {entity['opportunity_id']}")
        print(f"Opportunity Title: {entity['opportunity_title']}")
        print(f"Agency: {entity['agency']}")
        print(f"Summary: {entity['summary']['summary_description']}")
        print("---" * 20)
    if "response_llm" in result:
        print(result["response_llm"]["replies"][0].text)


def no_toolset_pipeline(question):
    pipeline = pipeline_wrapper.create_no_toolset_pipeline()
    user_input = ChatMessage.from_user(text=question)
    result = pipeline.run(
        {
            "llm": {"messages": [user_input]},
        }
    )
    logger.info("Result: %s", pformat(result))
    print(result["llm"]["replies"][0].text)


#


def agent(question):
    # This results into multiple threads in Phoenix logs, which is undesirable
    toolset = get_toolset()
    agent = Agent(
        # chat_generator=OpenAIChatGenerator(tools_strict=False), tools=toolset, exit_conditions=["text"]
        chat_generator=OpenAIChatGenerator(),
        tools=toolset,
        exit_conditions=["text"],
    )
    agent.warm_up()

    response = agent.run(messages=[ChatMessage.from_user(question)])
    logger.info("Response: %s", pformat(response))
    print(response["messages"][-1].text)


#

if __name__ == "__main__":
    # stdio()
    # streamable()

    # import asyncio
    # asyncio.run(client())

    # get_toolset()

    from common import haystack_utils, phoenix_utils

    haystack_utils.set_up_tracing()
    # phoenix_utils.configure_phoenix()
    # toolset_pipeline("yoom value of 2 and 3")
    # no_toolset_pipeline("yoom value of 2 and 3")
    # agent("yoom value of 2 and 3")

    pipeline_wrapper.ONLY_INVOKE_TOOL = True
    toolset_pipeline(
        "What grant opportunities are available for NASA? Make sure to provide the required 'pagination' parameter."
    )
    # agent("What grant opportunities are available for NASA?")
