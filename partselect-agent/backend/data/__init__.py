import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "partselect.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"

SYMPTOM_TO_PARTS_CTE = """
WITH RECURSIVE candidates AS (
    SELECT sf.part_number, sf.rank
    FROM symptom_fixes sf
    WHERE sf.symptom_id = ?
)
SELECT c.part_number, c.rank, co.confidence
FROM candidates c
JOIN compatibility co ON co.part_number = c.part_number
WHERE co.model_number = ?
  AND co.confidence IN ('confirmed', 'inferred')
ORDER BY c.rank
"""


def get_connection(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path = DB_PATH) -> None:
    schema = SCHEMA_PATH.read_text()
    with get_connection(db_path) as conn:
        conn.executescript(schema)
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
