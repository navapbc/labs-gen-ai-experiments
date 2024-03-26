#!/usr/bin/env python

from datetime import datetime
from dotenv import main
import operator
import json
from typing import TypedDict, Annotated, Sequence
# import os
import textwrap
import graphviz  # type: ignore

from langgraph.prebuilt import ToolInvocation  # type: ignore
from langgraph.prebuilt import ToolExecutor  # type: ignore
from langgraph.graph import StateGraph  # type: ignore
from langgraph.graph import END

from langchain.agents import load_tools

from engine import create_llm
from tool_calling import create_tool_calling_chain
from my_tools import (
    call_211_api,
    query_spreadsheet,
    merge_json_results,
)


# Inspired by https://python.langchain.com/docs/langgraph
# More documentation: https://blog.langchain.dev/langgraph/
class WorkflowState(TypedDict):
    final_answer: dict
    tool_responses: Annotated[dict, lambda d1, d2: d1 | d2]
    messages: Annotated[Sequence[dict], operator.add]


class MyWorkflow:

    def __init__(self, model_name: str, tools: list):
        main.load_dotenv()
        self.graph = self._init_graph()
        self.llm_chain = {}
        for tool in tools:
            self.llm_chain[tool.name] = create_tool_calling_chain(model_name, [tool])
        # tool_executor will be used to call the tool specified by the LLM in the llm_chain
        self.tool_executor = ToolExecutor(tools)


    def _init_graph(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("decision_node", self.check_for_final_answer)
        graph.add_node("run_llms", self.run_llms)
        graph.add_node("merge_tool_results", self.merge_results)

        # Set the entrypoint as `decision_node`
        graph.set_entry_point("decision_node")

        graph.add_conditional_edges("decision_node", self.decide_next_node)
        graph.add_edge("merge_tool_results", "decision_node")

        graph.add_node("llm_211_api", self.llm_211_api)
        graph.add_node("call_tool_211_api", self.call_211_tool)
        graph.add_edge("run_llms", "llm_211_api")
        graph.add_edge("llm_211_api", "call_tool_211_api")

        graph.add_node("llm_spreadsheet_query", self.llm_spreadsheet_query)
        graph.add_node("call_tool_spreadsheet", self.call_spreadsheet_tool)
        graph.add_edge("run_llms", "llm_spreadsheet_query")
        graph.add_edge("llm_spreadsheet_query", "call_tool_spreadsheet")

        graph.add_edge("call_tool_211_api", "decision_node")
        graph.add_edge("call_tool_spreadsheet", "decision_node")
        self._draw_graph(graph)
        return graph

    def _draw_graph(self, graph: StateGraph):
        g = graphviz.Digraph(filename="workflow.dot")
        g.node(END, shape="box")
        g.node("decision_node", style="filled", color="gray")
        for name, _ in graph.nodes.items():
            g.node(name)
        for n1, n2 in graph.edges:
            g.edge(n1, n2)
        # debug_here(locals())
        for n, branches in graph.branches.items():
            for bb in branches:
                g.edge(n, bb.condition.__name__, style="dotted")
        g.node("decide_next_node", shape="diamond")
        # Add edges based on decide_next_node() return value
        g.edge("decide_next_node", END, style="dotted")
        g.edge("decide_next_node", "merge_tool_results", style="dotted")
        g.edge("decide_next_node", "run_llms", style="dotted")
        # Paste printout into https://dreampuf.github.io/GraphvizOnline to visualize graph
        print(g.source)

    # Determines next node to call
    def decide_next_node(self, state):
        print("\nNEXT_EDGE") # , json.dumps(state, indent=2))

        if state["final_answer"]:
            return END

        if self._got_responses_from_all_tools(state):
            return "merge_tool_results"

        return "run_llms"

    def check_for_final_answer(self, state):
        print("\nHAS_FINAL_ANSWER node")  # , json.dumps(state, indent=2))

        last_message = state["messages"][-1]
        if "user_query" in last_message:
            return None

        if state["final_answer"]:
            return None

        if self._got_responses_from_all_tools(state):
            # Return a list for "messages" because it will get added to the existing list
            return {"messages": [{"log": "Got both responses"}]}

        # This doesn't occur probably b/c LangGraph waits for all incoming edges to be complete
        print("\nHAS_FINAL_ANSWER node: Waiting for more responses")

    def _got_responses_from_all_tools(self, state):
        expected_tools = [ "spreadsheet", "211_api" ]
        return all(key in state["tool_responses"] for key in expected_tools)

    def run_llms(self, state):
        print("\nRUN_LLMS node", state["messages"][-1])
        return None

    def llm_211_api(self, state):
        # find the last message that mentions the "user_query"
        user_message = next(m for m in reversed(state["messages"]) if "user_query" in m)
        print("\nLLM_211_API node", user_message)

        # Basic Human-in-the-loop example:
        # print("[y/n] continue with: call_211_api?")
        # response = input()
        # if response == "n":
        #     sys.exit()

        llm_response = self.invoke_user_message("call_211_api", user_message)
        return {"messages": [llm_response]}

    def llm_spreadsheet_query(self, state):
        # find the last message that mentions the "user_query"
        user_message = next(m for m in reversed(state["messages"]) if "user_query" in m)
        print("\nLLM_SPREADSHEET_QUERY node", user_message)
        llm_response = self.invoke_user_message("query_spreadsheet", user_message)
        return {"messages": [llm_response]}

    def invoke_user_message(self, tool, user_message): 
        return self.llm_chain[tool].invoke(user_message)

    def call_211_tool(self, state):
        response = self._call_tool(toolname="call_211_api", state=state)
        return {"tool_responses": {"211_api": response}}

    def call_spreadsheet_tool(self, state):
        response = self._call_tool(toolname="query_spreadsheet", state=state)
        return {"tool_responses": {"spreadsheet": response}}

    def _call_tool(self, toolname, state):
        messages = state["messages"]
        # find the last message that mentions the tool
        tool_message = next(
            m for m in reversed(messages) if "tool" in m and m["tool"] == toolname
        )
        # Print time to ensure that tools are called in parallel and don't block each other
        print(f"\nCALL_TOOL {toolname} {datetime.now().strftime('%H:%M:%S')}:")
        tool_invoc = ToolInvocation(
            tool=tool_message["tool"], tool_input=tool_message["tool_input"]
        )
        # call the tool_executor and get back a response
        response = self.tool_executor.invoke(tool_invoc)
        resp_obj = {"tool_used": tool_message["tool"], "tool_result": response}
        # return a list, because this will get added to the existing list
        print(f"\nResult from {toolname} {datetime.now().strftime('%H:%M:%S')}:")
        print(resp_obj)  # textwrap.shorten(str(resp_obj), width=150)
        return resp_obj

    def merge_results(self, state):
        # For now, manually set tool_input instead of using an LLM
        # Find the last message that mentions the "user_query"
        user_message = next(m for m in reversed(state["messages"]) if "user_query" in m)
        tool_input_dict = {
            "user_query": user_message["user_query"],
            "result_211_api": state["tool_responses"]["211_api"]["tool_result"],
            "result_spreadsheet": state["tool_responses"]["spreadsheet"]["tool_result"],
        }
        mocked_state = {
            "messages": [
                {
                    "tool": "merge_json_results",
                    "tool_input": tool_input_dict,
                }
            ]
        }
        # print("\nMERGE_RESULTS node", json.dumps(mocked_state, indent=2))

        merged_results = self._call_tool(
            toolname="merge_json_results", state=mocked_state
        )
        json_obj = merged_results["tool_result"]
        # print("\nMERGE_RESULTS response:", json.dumps(json_obj, indent=2))
        if not json_obj:
            json_obj = "None found"

        return {"final_answer": json_obj}


math_llm = create_llm(model_name="openhermes", settings={"temperature": 0.1})
loaded_tools = load_tools(["llm-math"], llm=math_llm)
some_tools = [
    merge_json_results,
    call_211_api,
    query_spreadsheet,
] + loaded_tools

workflow = MyWorkflow("openhermes", some_tools)
# This compiles it into a LangChain Runnable,
runnable_graph = workflow.graph.compile()

user_input = input("Query (press Enter to use the default query): ")
if not user_input:
    # user_input = "what is the weather in sf"
    # user_input = "what is 2 + 8"
    # user_input = "list financial support in michigan"
    # user_input = "list consumer services in Detroit"
    # user_input = "list food assistance in NYC"
    # user_input = "list food assistance and homeless services in Queens, NY"
    user_input = "list food assistance, affordable childcare options, information on parental leave policies, postpartum support groups in Queens, NY for parents with a newborn baby and monthly total income of $6000"
    # user_input = "list affordable childcare options, information on parental leave policies, postpartum support groups in Queens, NY for parents with a newborn baby and monthly total income of $6000"

inputs = {"messages": [{"user_query": user_input}]}
final_state = runnable_graph.invoke(inputs)
# print("\nFINAL_STATE", type(final_state), final_state)
print("\nFINAL_ANSWER")
print(final_state['final_answer'])

