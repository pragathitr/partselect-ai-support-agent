import sqlite3
from typing import Optional
from ._connection import get_connection


def _clean_identifier(value: str) -> str:
    """Normalize user-provided part/model identifiers for exact lookups."""
    return value.strip().strip("?.!,;:").upper()


def search_parts(
    query: str,
    appliance_type: Optional[str] = None,
    limit: int = 5,
    conn: Optional[sqlite3.Connection] = None,
) -> list[dict]:
    """Search parts by name, description, or OEM part number."""
    _close = conn is None
    if conn is None:
        conn = get_connection()
    try:
        like = f"%{query}%"
        if appliance_type:
            sql = """
                SELECT p.part_number, p.name, p.brand, p.price, p.in_stock,
                       p.mfr_part_number, p.description, ac.slug AS appliance_type
                FROM parts p
                JOIN appliance_categories ac ON ac.id = p.category_id
                WHERE ac.slug = ?
                  AND (p.name LIKE ? OR p.description LIKE ? OR p.mfr_part_number LIKE ?)
                ORDER BY p.name
                LIMIT ?
            """
            rows = conn.execute(sql, (appliance_type, like, like, like, limit)).fetchall()
        else:
            sql = """
                SELECT p.part_number, p.name, p.brand, p.price, p.in_stock,
                       p.mfr_part_number, p.description, ac.slug AS appliance_type
                FROM parts p
                JOIN appliance_categories ac ON ac.id = p.category_id
                WHERE p.name LIKE ? OR p.description LIKE ? OR p.mfr_part_number LIKE ?
                ORDER BY p.name
                LIMIT ?
            """
            rows = conn.execute(sql, (like, like, like, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        if _close:
            conn.close()


def get_part_detail(
    part_number: str,
    conn: Optional[sqlite3.Connection] = None,
) -> Optional[dict]:
    """Fetch a part by PS number or OEM part number. Returns None if not found."""
    part_number = _clean_identifier(part_number)
    _close = conn is None
    if conn is None:
        conn = get_connection()
    try:
        sql = """
            SELECT p.part_number, p.name, p.brand, p.price, p.in_stock,
                   p.mfr_part_number, p.description, p.image_url,
                   ac.slug AS appliance_type
            FROM parts p
            JOIN appliance_categories ac ON ac.id = p.category_id
            WHERE p.part_number = ? OR p.mfr_part_number = ?
            LIMIT 1
        """
        row = conn.execute(sql, (part_number, part_number)).fetchone()
        return dict(row) if row else None
    finally:
        if _close:
            conn.close()


def check_compatibility(
    part_number: str,
    model_number: str,
    conn: Optional[sqlite3.Connection] = None,
) -> dict:
    """Check whether a part is compatible with a model.

    Returns:
        {"compatible": bool, "confidence": "confirmed" | "inferred" | "unknown"}
    """
    part_number = _clean_identifier(part_number)
    model_number = _clean_identifier(model_number)
    _close = conn is None
    if conn is None:
        conn = get_connection()
    try:
        row = conn.execute(
            "SELECT confidence FROM compatibility WHERE part_number = ? AND model_number = ?",
            (part_number, model_number),
        ).fetchone()
        if row:
            return {"compatible": True, "confidence": row["confidence"]}

        # Detect cross-appliance mismatch explicitly so the specialist can give
        # a definitive answer rather than hedging on "unknown".
        mismatch = conn.execute(
            """
            SELECT p_cat.slug AS part_appliance, m_cat.slug AS model_appliance
            FROM parts p
            JOIN appliance_categories p_cat ON p_cat.id = p.category_id
            JOIN models m ON m.model_number = ?
            JOIN appliance_categories m_cat ON m_cat.id = m.category_id
            WHERE p.part_number = ?
            """,
            (model_number, part_number),
        ).fetchone()
        if mismatch and mismatch["part_appliance"] != mismatch["model_appliance"]:
            return {
                "compatible": False,
                "confidence": "incompatible_appliance_type",
                "part_appliance": mismatch["part_appliance"],
                "model_appliance": mismatch["model_appliance"],
            }

        return {"compatible": False, "confidence": "unknown"}
    finally:
        if _close:
            conn.close()


def get_compatible_models(
    part_number: str,
    conn: Optional[sqlite3.Connection] = None,
) -> list[dict]:
    """Return all models a part is known to fit."""
    part_number = _clean_identifier(part_number)
    _close = conn is None
    if conn is None:
        conn = get_connection()
    try:
        sql = """
            SELECT m.model_number, m.brand, m.display_name,
                   ac.slug AS appliance_type, c.confidence
            FROM compatibility c
            JOIN models m ON m.model_number = c.model_number
            JOIN appliance_categories ac ON ac.id = m.category_id
            WHERE c.part_number = ?
            ORDER BY c.confidence DESC, m.model_number
        """
        rows = conn.execute(sql, (part_number,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        if _close:
            conn.close()
