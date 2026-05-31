"""
Public interface for the PartSelect LangGraph agent.

Usage:
    from backend.agent import run_agent

    result = run_agent("My Whirlpool WRF555SDFZ ice maker stopped working")
    print(result["messages"][-1].content)
    print(result["validator_verdict"])
"""
from __future__ import annotations

import uuid

from langchain_core.messages import HumanMessage

from .graph import graph
from .state import AgentState


def run_agent(
    user_message: str,
    history: list | None = None,
    conversation_id: str | None = None,
) -> AgentState:
    """Invoke the agent graph for a single user turn.

    Args:
        user_message:    The customer's message.
        history:         Prior BaseMessage objects for multi-turn context (optional).
        conversation_id: Opaque ID for persistence; auto-generated if omitted.

    Returns:
        The final AgentState dict with messages, appliance_type, validator_verdict, etc.
    """
    initial: AgentState = {
        "messages": (history or []) + [HumanMessage(content=user_message)],
        "appliance_type": None,
        "model_number": None,
        "validator_verdict": None,
        "validator_feedback": None,
        "conversation_id": conversation_id or str(uuid.uuid4()),
    }
    return graph.invoke(initial)
