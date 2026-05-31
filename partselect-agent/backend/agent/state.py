from typing import Annotated, Literal, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    # Full conversation history — add_messages reducer appends incoming messages
    messages: Annotated[list[BaseMessage], add_messages]
    # Set by the supervisor node on every turn
    appliance_type: Optional[Literal["refrigerator", "dishwasher", "unknown"]]
    model_number: Optional[str]
    # True when the question is outside refrigerators / dishwashers
    is_out_of_scope: Optional[bool]
    # Set by the validator node
    validator_verdict: Optional[Literal["pass", "warn", "escalate"]]
    validator_feedback: Optional[str]
    # Opaque ID for conversation persistence (used by FastAPI layer)
    conversation_id: Optional[str]
