import json

from langchain.prompts import BasePromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableLambda

from engine import create_llm

from debugging import debug_runnable


def create_tool_calling_chain(model_name: str, tools: list):
    """Create a chain that uses an LLM to interpret the user's prompt and returns a tool to call along with the tool's input."""
    prompt = _agent_prompt_template(tools)

    return (
        {"input": lambda last_message: last_message["user_query"]}
        | prompt
        | debug_runnable("  Tooling PROMPT")
        | create_llm(model_name=model_name, settings={"temperature": 0.1, "top_p": 0.8})
        | RunnableLambda(_parse_llm_output)
        # | debug_runnable("4")
    )


def _agent_prompt_template(tools: list):
    # Compare with https://smith.langchain.com/hub/search?q=hwchase17%2Fopenai-tools-agent
    template = """You are a helpful automated agent with tools. Answer the question with a JSON that specifies the tool and tool input.

You have access to the following tools:

{tools}

In order to use a tool, you can use "tool" and "tool_input" JSON keys.
For example, if you have a tool called 'search' that could run a google search, in order to search for the weather in SF you would respond with a JSON object:

{{ "tool": "search", "tool_input": "weather in SF" }}

Begin!

Question: {input}
"""
    prompt: BasePromptTemplate = PromptTemplate.from_template(template)

    if tools:
        prompt = prompt.partial(tools=_describe_tools(tools))
    return prompt


def _parse_llm_output(text: str) -> dict:
    print("  LLM_OUTPUT:", text)
    jsondict = json.loads(text)
    # print("jsondict", jsondict)
    if "tool" in jsondict:
        _tool = jsondict["tool"]
        _tool_input = jsondict.get("tool_input", "")
        if isinstance(_tool_input, list):
            _tool_input = ",".join(_tool_input)
        return {"tool": _tool, "tool_input": _tool_input}
    else:
        # To trigger, ask: what tools are available
        print("!!!!!!!!!!!!!!!!")
        return {"output": text}
        # raise ValueError


def _describe_tools(tools):
    """Convert tools into a string that goes into the prompt"""
    return "\n".join([f"- {tool.name}: {tool.description}" for tool in tools])
