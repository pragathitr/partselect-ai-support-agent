"""Conversation persistence backed by the normalized SQLite schema."""
from __future__ import annotations

import json
import sqlite3
from typing import Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from backend.data import SCHEMA_PATH
from backend.tools._connection import get_connection


def init_table(conn: Optional[sqlite3.Connection] = None) -> None:
    """Ensure the conversations/messages tables from schema.sql exist."""
    own = conn is None
    if own:
        conn = get_connection()
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        order_cols = {
            row["name"] for row in conn.execute("PRAGMA table_info(orders)").fetchall()
        }
        if "customer_email" not in order_cols:
            conn.execute("ALTER TABLE orders ADD COLUMN customer_email TEXT")
        conn.executemany(
            "UPDATE orders SET customer_email = ? WHERE order_id = ? AND customer_email IS NULL",
            [
                ("demo@example.com", "12345"),
                ("demo@example.com", "12346"),
                ("customer@example.com", "12347"),
                ("shopper@example.com", "12348"),
                ("parts@example.com", "12349"),
            ],
        )
        conn.commit()
    finally:
        if own:
            conn.close()


def _message_role(message: BaseMessage) -> Optional[str]:
    if isinstance(message, HumanMessage):
        return "human"
    if isinstance(message, AIMessage):
        return "ai"
    return None


def save_turn(
    conversation_id: str,
    messages: list[BaseMessage],
    metadata: dict,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    own = conn is None
    if own:
        conn = get_connection()

    try:
        conn.execute(
            """
            INSERT INTO conversations (id, appliance_type, model_number)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                appliance_type = excluded.appliance_type,
                model_number = excluded.model_number
            """,
            (
                conversation_id,
                metadata.get("appliance_type"),
                metadata.get("model_number"),
            ),
        )
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))

        for message in messages:
            role = _message_role(message)
            if role is None:
                continue

            content = message.content if isinstance(message.content, str) else str(message.content)
            tool_calls = getattr(message, "tool_calls", None)
            conn.execute(
                """
                INSERT INTO messages (
                    conversation_id,
                    role,
                    content,
                    tool_calls_json,
                    validator_verdict
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    role,
                    content,
                    json.dumps(tool_calls) if tool_calls else None,
                    metadata.get("validator_verdict") if role == "ai" else None,
                ),
            )

        conn.commit()
    finally:
        if own:
            conn.close()


def load_history(
    conversation_id: str,
    conn: Optional[sqlite3.Connection] = None,
) -> list[BaseMessage]:
    own = conn is None
    if own:
        conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT role, content
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id
            """,
            (conversation_id,),
        ).fetchall()

        history: list[BaseMessage] = []
        for row in rows:
            if row["role"] == "human":
                history.append(HumanMessage(content=row["content"]))
            elif row["role"] == "ai":
                history.append(AIMessage(content=row["content"]))
        return history
    finally:
        if own:
            conn.close()


def list_conversations(
    limit: int = 20,
    conn: Optional[sqlite3.Connection] = None,
) -> list[dict]:
    own = conn is None
    if own:
        conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                c.id,
                c.created_at,
                c.appliance_type,
                c.model_number,
                MAX(m.created_at) AS updated_at
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
            GROUP BY c.id
            ORDER BY COALESCE(updated_at, c.created_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            {
                "id": row["id"],
                "metadata": {
                    "appliance_type": row["appliance_type"],
                    "model_number": row["model_number"],
                },
                "created_at": row["created_at"],
                "updated_at": row["updated_at"] or row["created_at"],
            }
            for row in rows
        ]
    finally:
        if own:
            conn.close()
