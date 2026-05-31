"""
LangGraph state graph for the PartSelect agent.

Flow (in-scope):
    START → supervisor → specialist ──(tool calls)──► tool_node → specialist (loop)
                                    └─(final answer)─► validator → END

Flow (out-of-scope):
    START → supervisor → decline → END
"""
from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from .nodes import decline_node, specialist_node, supervisor_node, validator_node
from .state import AgentState
from .tools_schema import ALL_TOOLS


def _route_after_supervisor(state: AgentState) -> Literal["specialist", "decline"]:
    """Short-circuit to decline for out-of-scope questions."""
    if state.get("is_out_of_scope"):
        return "decline"
    return "specialist"


def _route_after_specialist(state: AgentState) -> Literal["tool_node", "validator"]:
    """Send to ToolNode if the model issued tool calls; otherwise go to validator."""
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tool_node"
    return "validator"


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("decline", decline_node)
    builder.add_node("specialist", specialist_node)
    builder.add_node("tool_node", ToolNode(ALL_TOOLS))
    builder.add_node("validator", validator_node)

    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {"specialist": "specialist", "decline": "decline"},
    )
    builder.add_conditional_edges(
        "specialist",
        _route_after_specialist,
        {"tool_node": "tool_node", "validator": "validator"},
    )
    builder.add_edge("tool_node", "specialist")
    builder.add_edge("decline", END)
    builder.add_edge("validator", END)

    return builder


# Compiled graph — imported by FastAPI and tests
graph = build_graph().compile()
