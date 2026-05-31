"""FastAPI routes: chat, stream sessions, SSE, and conversation management."""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import AsyncIterator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.agent import run_agent
from backend.agent.graph import graph
from backend.agent.state import AgentState

from .persistence import list_conversations, load_history, save_turn
from .security import require_api_key

router = APIRouter(prefix="/api")
_STREAM_SESSIONS: dict[str, ChatRequest] = {}


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    appliance_type: Optional[str] = None
    model_number: Optional[str] = None
    validator_verdict: Optional[str] = None
    validator_feedback: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _last_ai_text(messages: list) -> str:
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content if isinstance(msg.content, str) else str(msg.content)
    return ""


def _meta_from_state(state: AgentState) -> dict:
    return {
        "appliance_type": state.get("appliance_type"),
        "model_number": state.get("model_number"),
        "validator_verdict": state.get("validator_verdict"),
        "validator_feedback": state.get("validator_feedback"),
    }


# ---------------------------------------------------------------------------
# POST /api/chat — blocking full-graph response
# ---------------------------------------------------------------------------


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_api_key)])
async def chat(req: ChatRequest) -> ChatResponse:
    cid = req.conversation_id or str(uuid.uuid4())
    history = load_history(cid)

    result: AgentState = await asyncio.to_thread(
        run_agent, req.message, history=history, conversation_id=cid
    )

    save_turn(cid, result["messages"], _meta_from_state(result))

    return ChatResponse(
        conversation_id=cid,
        answer=_last_ai_text(result["messages"]),
        **_meta_from_state(result),
    )


# ---------------------------------------------------------------------------
# POST /api/chat/stream-session creates a token; GET /api/chat/stream streams SSE.
# ---------------------------------------------------------------------------


@router.post("/chat/stream-session", dependencies=[Depends(require_api_key)])
async def create_chat_stream_session(req: ChatRequest) -> dict:
    token = str(uuid.uuid4())
    _STREAM_SESSIONS[token] = req
    return {"stream_token": token}


@router.get("/chat/stream")
async def chat_stream(stream_token: str = Query(...)):
    req = _STREAM_SESSIONS.pop(stream_token, None)
    if req is None:
        raise HTTPException(status_code=404, detail="Stream session not found")

    cid = req.conversation_id or str(uuid.uuid4())
    history = load_history(cid)

    initial: AgentState = {
        "messages": (history or []) + [HumanMessage(content=req.message)],
        "appliance_type": None,
        "model_number": None,
        "validator_verdict": None,
        "validator_feedback": None,
        "conversation_id": cid,
    }

    async def generate() -> AsyncIterator[dict]:
        # Track accumulated state for persistence after stream completes
        all_messages: list = list(initial["messages"])
        meta: dict = {
            "appliance_type": None,
            "model_number": None,
            "validator_verdict": None,
            "validator_feedback": None,
        }

        try:
            stream = graph.astream(initial, stream_mode="updates")
            async for chunk in stream:
                for node_name, updates in chunk.items():
                    # Accumulate
                    if "messages" in updates:
                        all_messages.extend(updates["messages"])
                    for k in meta:
                        if updates.get(k) is not None:
                            meta[k] = updates[k]

                    # Build per-node SSE payload
                    payload: dict = {"node": node_name}

                    if node_name == "supervisor":
                        payload["appliance_type"] = updates.get("appliance_type")
                        payload["model_number"] = updates.get("model_number")

                    elif node_name in ("specialist", "decline"):
                        for msg in updates.get("messages", []):
                            if isinstance(msg, AIMessage):
                                if msg.tool_calls:
                                    payload["tool_calls"] = [
                                        {"name": tc["name"], "args": tc["args"]}
                                        for tc in msg.tool_calls
                                    ]
                                elif msg.content:
                                    payload["content"] = (
                                        msg.content
                                        if isinstance(msg.content, str)
                                        else str(msg.content)
                                    )

                    elif node_name == "tool_node":
                        payload["tool_results"] = [
                            {
                                "name": getattr(m, "name", ""),
                                "content": m.content if isinstance(m.content, str) else str(m.content),
                            }
                            for m in updates.get("messages", [])
                            if isinstance(m, ToolMessage)
                        ]

                    elif node_name == "validator":
                        payload["verdict"] = updates.get("validator_verdict")
                        payload["feedback"] = updates.get("validator_feedback")
                        # When escalated, include the replacement message so the
                        # frontend can overwrite the specialist's unsafe content.
                        override_msgs = updates.get("messages", [])
                        if override_msgs:
                            last_msg = override_msgs[-1]
                            payload["override_content"] = (
                                last_msg.content
                                if isinstance(last_msg.content, str)
                                else str(last_msg.content)
                            )

                    yield {"event": node_name, "data": json.dumps(payload)}
        except Exception:
            yield {
                "event": "error",
                "data": json.dumps({
                    "message": "The assistant hit a server-side configuration or tool error.",
                    "conversation_id": cid,
                }),
            }
            return

        # Persist full conversation after stream finishes
        save_turn(cid, all_messages, meta)

        yield {
            "event": "done",
            "data": json.dumps({"conversation_id": cid, **meta}),
        }

    return EventSourceResponse(generate())


# ---------------------------------------------------------------------------
# Conversation management endpoints
# ---------------------------------------------------------------------------


@router.get("/conversations", dependencies=[Depends(require_api_key)])
async def get_conversations(limit: int = 20) -> list[dict]:
    return list_conversations(limit=limit)


@router.get("/conversations/{conversation_id}", dependencies=[Depends(require_api_key)])
async def get_conversation(conversation_id: str) -> dict:
    history = load_history(conversation_id)
    if not history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "role": "human" if isinstance(m, HumanMessage) else "ai",
                "content": m.content if isinstance(m.content, str) else str(m.content),
            }
            for m in history
            if isinstance(m, (HumanMessage, AIMessage))
        ],
    }


@router.delete(
    "/conversations/{conversation_id}",
    status_code=204,
    dependencies=[Depends(require_api_key)],
)
async def delete_conversation(conversation_id: str) -> None:
    from backend.tools._connection import get_connection

    conn = get_connection()
    try:
        conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        conn.commit()
    finally:
        conn.close()
