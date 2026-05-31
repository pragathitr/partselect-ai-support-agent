"""Tests for Phase 4: FastAPI routes and conversation persistence."""
from __future__ import annotations

import json
import sqlite3
import uuid

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

from backend.agent.graph import graph
from backend.api.persistence import init_table, list_conversations, load_history, save_turn


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mem_db():
    """In-memory SQLite for persistence tests (isolated from the real DB)."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_table(conn=conn)
    yield conn
    conn.close()


@pytest.fixture()
def client():
    from backend.main import app

    return TestClient(app)


# ---------------------------------------------------------------------------
# Persistence unit tests
# ---------------------------------------------------------------------------


def test_init_table_idempotent(mem_db):
    init_table(conn=mem_db)
    init_table(conn=mem_db)  # second call must not raise


def test_save_and_load_round_trip(mem_db):
    cid = str(uuid.uuid4())
    messages = [HumanMessage(content="hello"), AIMessage(content="hi")]
    save_turn(cid, messages, {"appliance_type": "refrigerator"}, conn=mem_db)

    loaded = load_history(cid, conn=mem_db)
    assert len(loaded) == 2
    assert isinstance(loaded[0], HumanMessage)
    assert loaded[0].content == "hello"
    assert isinstance(loaded[1], AIMessage)
    assert loaded[1].content == "hi"


def test_load_history_missing_returns_empty(mem_db):
    result = load_history("nonexistent-id", conn=mem_db)
    assert result == []


def test_save_turn_upsert(mem_db):
    cid = str(uuid.uuid4())
    save_turn(cid, [HumanMessage(content="first")], {}, conn=mem_db)
    save_turn(
        cid,
        [HumanMessage(content="first"), AIMessage(content="second")],
        {"appliance_type": "dishwasher"},
        conn=mem_db,
    )
    loaded = load_history(cid, conn=mem_db)
    assert len(loaded) == 2
    assert loaded[1].content == "second"


def test_list_conversations_ordering(mem_db):
    for i in range(3):
        save_turn(str(i), [HumanMessage(content=f"msg{i}")], {}, conn=mem_db)
    results = list_conversations(limit=10, conn=mem_db)
    assert len(results) == 3


def test_list_conversations_limit(mem_db):
    for i in range(5):
        save_turn(str(i), [HumanMessage(content=f"msg{i}")], {}, conn=mem_db)
    results = list_conversations(limit=2, conn=mem_db)
    assert len(results) == 2


def test_list_conversations_metadata_parsed(mem_db):
    cid = str(uuid.uuid4())
    save_turn(cid, [HumanMessage(content="x")], {"appliance_type": "refrigerator"}, conn=mem_db)
    results = list_conversations(limit=1, conn=mem_db)
    assert results[0]["metadata"]["appliance_type"] == "refrigerator"


# ---------------------------------------------------------------------------
# HTTP route tests (agent mocked — no real LLM calls)
# ---------------------------------------------------------------------------


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_chat_returns_answer(client, mocker):
    fake = {
        "messages": [HumanMessage(content="test q"), AIMessage(content="Here is the answer.")],
        "appliance_type": "refrigerator",
        "model_number": "WRF555SDFZ",
        "validator_verdict": "pass",
        "validator_feedback": "Accurate.",
        "conversation_id": "cid-1",
    }
    mocker.patch("backend.api.routes.run_agent", return_value=fake)
    mocker.patch("backend.api.routes.load_history", return_value=[])
    mocker.patch("backend.api.routes.save_turn")

    r = client.post("/api/chat", json={"message": "My fridge is leaking"})
    assert r.status_code == 200
    data = r.json()
    assert data["answer"] == "Here is the answer."
    assert data["appliance_type"] == "refrigerator"
    assert data["model_number"] == "WRF555SDFZ"
    assert data["validator_verdict"] == "pass"
    assert "conversation_id" in data


def test_chat_generates_new_conversation_id(client, mocker):
    fake = {
        "messages": [AIMessage(content="Hello!")],
        "appliance_type": "unknown",
        "model_number": None,
        "validator_verdict": "pass",
        "validator_feedback": "Fine.",
        "conversation_id": None,
    }
    mocker.patch("backend.api.routes.run_agent", return_value=fake)
    mocker.patch("backend.api.routes.load_history", return_value=[])
    mocker.patch("backend.api.routes.save_turn")

    r = client.post("/api/chat", json={"message": "hi"})
    assert r.status_code == 200
    assert r.json()["conversation_id"]  # non-empty, auto-generated


def test_chat_uses_provided_conversation_id(client, mocker):
    fake = {
        "messages": [AIMessage(content="Hi!")],
        "appliance_type": "unknown",
        "model_number": None,
        "validator_verdict": "pass",
        "validator_feedback": "Fine.",
        "conversation_id": "my-cid-123",
    }
    mocker.patch("backend.api.routes.run_agent", return_value=fake)
    mocker.patch("backend.api.routes.load_history", return_value=[])
    mocker.patch("backend.api.routes.save_turn")

    r = client.post("/api/chat", json={"message": "hi", "conversation_id": "my-cid-123"})
    assert r.status_code == 200
    assert r.json()["conversation_id"] == "my-cid-123"


def test_chat_loads_history(client, mocker):
    """Existing history is passed to run_agent."""
    prior = [HumanMessage(content="prior turn"), AIMessage(content="prior answer")]
    mocker.patch("backend.api.routes.load_history", return_value=prior)
    mock_agent = mocker.patch(
        "backend.api.routes.run_agent",
        return_value={
            "messages": prior + [AIMessage(content="new answer")],
            "appliance_type": None,
            "model_number": None,
            "validator_verdict": "pass",
            "validator_feedback": "",
            "conversation_id": "cid",
        },
    )
    mocker.patch("backend.api.routes.save_turn")

    client.post("/api/chat", json={"message": "follow up", "conversation_id": "cid"})

    call_kwargs = mock_agent.call_args
    assert call_kwargs[1]["history"] == prior


def test_get_conversation_returns_messages(client, mocker):
    messages = [HumanMessage(content="hello"), AIMessage(content="world")]
    mocker.patch("backend.api.routes.load_history", return_value=messages)

    r = client.get("/api/conversations/some-id")
    assert r.status_code == 200
    data = r.json()
    assert data["conversation_id"] == "some-id"
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "human"
    assert data["messages"][0]["content"] == "hello"
    assert data["messages"][1]["role"] == "ai"


def test_get_conversation_not_found(client, mocker):
    mocker.patch("backend.api.routes.load_history", return_value=[])
    r = client.get("/api/conversations/missing-id")
    assert r.status_code == 404


def test_list_conversations_endpoint(client, mocker):
    mocker.patch(
        "backend.api.routes.list_conversations",
        return_value=[
            {"id": "a", "metadata": {}, "created_at": "2024-01-01T00:00:00+00:00", "updated_at": "2024-01-01T00:00:00+00:00"},
            {"id": "b", "metadata": {}, "created_at": "2024-01-02T00:00:00+00:00", "updated_at": "2024-01-02T00:00:00+00:00"},
        ],
    )
    r = client.get("/api/conversations")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_delete_conversation(client, mocker):
    # get_connection is imported inside the route function, so patch at source
    mock_conn = mocker.MagicMock()
    mocker.patch("backend.tools._connection.get_connection", return_value=mock_conn)

    r = client.delete("/api/conversations/some-id")
    assert r.status_code == 204


def test_chat_stream_returns_sse(client, mocker):
    """POST creates a stream session; GET streams SSE by opaque token."""

    async def fake_astream(initial, stream_mode=None):
        yield {"supervisor": {"appliance_type": "refrigerator", "model_number": None}}
        yield {
            "specialist": {
                "messages": [AIMessage(content="Your fridge needs a new door seal.")],
            }
        }
        yield {
            "validator": {
                "validator_verdict": "pass",
                "validator_feedback": "Accurate.",
            }
        }

    mocker.patch.object(graph, "astream", fake_astream)
    mocker.patch("backend.api.routes.load_history", return_value=[])
    mocker.patch("backend.api.routes.save_turn")

    session = client.post("/api/chat/stream-session", json={"message": "my fridge leaks"})
    assert session.status_code == 200
    token = session.json()["stream_token"]

    with client.stream("GET", "/api/chat/stream", params={"stream_token": token}) as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        body = r.read().decode()

    assert "supervisor" in body
    assert "refrigerator" in body
    assert "specialist" in body
    assert "validator" in body
    assert "done" in body


def test_chat_stream_invalid_token_returns_404(client):
    r = client.get("/api/chat/stream", params={"stream_token": "missing"})
    assert r.status_code == 404


def test_auth_required_when_api_key_configured(client, monkeypatch):
    monkeypatch.setenv("APP_API_KEY", "secret")
    r = client.post("/api/chat", json={"message": "hi"})
    assert r.status_code == 401

    r = client.post("/api/chat", json={"message": "hi"}, headers={"X-API-Key": "wrong"})
    assert r.status_code == 401
