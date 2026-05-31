import sqlite3
from typing import Optional
from ._connection import get_connection


def _clean_identifier(value: str) -> str:
    return value.strip().strip("?.!,;:")


def get_order_status(
    order_id: str,
    customer_email: str,
    conn: Optional[sqlite3.Connection] = None,
) -> Optional[dict]:
    """Look up order status by order ID and customer email."""
    order_id = _clean_identifier(order_id)
    customer_email = customer_email.strip().strip("?.!,;:").lower()
    _close = conn is None
    if conn is None:
        conn = get_connection()
    try:
        row = conn.execute(
            "SELECT order_id, part_number, status, tracking_number, estimated_delivery "
            "FROM orders WHERE order_id = ? AND LOWER(customer_email) = ?",
            (order_id, customer_email),
        ).fetchone()
        return dict(row) if row else None
    finally:
        if _close:
            conn.close()
