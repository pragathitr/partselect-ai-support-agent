import sqlite3
from typing import Optional
from ._connection import get_connection


def list_symptoms(
    appliance_type: str,
    conn: Optional[sqlite3.Connection] = None,
) -> list[dict]:
    """Return all symptom IDs and descriptions for an appliance type.

    Used to discover valid symptom_id values before calling diagnose_symptom.
    """
    _close = conn is None
    if conn is None:
        conn = get_connection()
    try:
        sql = """
            SELECT s.id, s.description, s.is_safety_critical
            FROM symptoms s
            JOIN appliance_categories ac ON ac.id = s.category_id
            WHERE ac.slug = ?
            ORDER BY s.id
        """
        rows = conn.execute(sql, (appliance_type,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        if _close:
            conn.close()


def diagnose_symptom(
    symptom_id: str,
    model_number: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> list[dict]:
    """Return ranked parts that fix a symptom, optionally filtered to a specific model.

    Without model_number: returns all parts linked to the symptom (ranked).
    With model_number: only returns parts that are also compatible with that model,
    adding the compatibility confidence level.
    """
    _close = conn is None
    if conn is None:
        conn = get_connection()
    try:
        if model_number:
            sql = """
                WITH candidates AS (
                    SELECT sf.part_number, sf.rank
                    FROM symptom_fixes sf
                    WHERE sf.symptom_id = ?
                )
                SELECT c.part_number, c.rank, co.confidence,
                       p.name, p.price, p.in_stock, p.mfr_part_number, p.brand
                FROM candidates c
                JOIN compatibility co ON co.part_number = c.part_number
                JOIN parts p ON p.part_number = c.part_number
                WHERE co.model_number = ?
                  AND co.confidence IN ('confirmed', 'inferred')
                ORDER BY c.rank
            """
            rows = conn.execute(sql, (symptom_id, model_number)).fetchall()
        else:
            sql = """
                SELECT sf.part_number, sf.rank,
                       p.name, p.price, p.in_stock, p.mfr_part_number, p.brand
                FROM symptom_fixes sf
                JOIN parts p ON p.part_number = sf.part_number
                WHERE sf.symptom_id = ?
                ORDER BY sf.rank
            """
            rows = conn.execute(sql, (symptom_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        if _close:
            conn.close()
