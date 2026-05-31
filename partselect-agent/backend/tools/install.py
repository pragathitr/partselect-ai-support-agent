import sqlite3
from typing import Optional
from ._connection import get_connection


def get_install_guide(
    part_number: str,
    conn: Optional[sqlite3.Connection] = None,
) -> list[dict]:
    """Return ordered installation steps for a part. Empty list if none exist."""
    _close = conn is None
    if conn is None:
        conn = get_connection()
    try:
        sql = """
            SELECT step_order, instruction, tool_required, safety_note
            FROM install_guides
            WHERE part_number = ?
            ORDER BY step_order
        """
        rows = conn.execute(sql, (part_number,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        if _close:
            conn.close()
