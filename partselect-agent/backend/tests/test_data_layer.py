"""
Phase 1 — Data layer unit tests.
All 8 tests use in-memory fixtures (no LLM calls, <5s wall clock).
"""
import sqlite3

import pytest

from backend.data import SYMPTOM_TO_PARTS_CTE


# ---------------------------------------------------------------------------
# 1. Recursive CTE — happy path
# ---------------------------------------------------------------------------

def test_recursive_cte_symptom_to_parts_to_models(db: sqlite3.Connection) -> None:
    """
    symptom SY_FRIDGE_ICE_MAKER_FAIL + model WRF555SDFZ should return
    the ranked candidate parts that fix the symptom AND fit the model.
    """
    rows = db.execute(
        SYMPTOM_TO_PARTS_CTE, ("SY_FRIDGE_ICE_MAKER_FAIL", "WRF555SDFZ")
    ).fetchall()

    part_numbers = [r["part_number"] for r in rows]
    assert len(rows) > 0, "CTE should return at least one result"
    assert "PS11769116" in part_numbers, "Ice maker assembly should be rank-1 fix"
    # Results must be ordered by rank
    ranks = [r["rank"] for r in rows]
    assert ranks == sorted(ranks), "Results must be ordered by rank (ascending)"


# ---------------------------------------------------------------------------
# 2. Recursive CTE — unknown symptom returns empty, not an error
# ---------------------------------------------------------------------------

def test_recursive_cte_returns_empty_not_error_for_unknown_symptom(
    db: sqlite3.Connection,
) -> None:
    rows = db.execute(
        SYMPTOM_TO_PARTS_CTE, ("SY_UNKNOWN_DOES_NOT_EXIST", "WRF555SDFZ")
    ).fetchall()
    assert rows == [], "Unknown symptom should return an empty list, not raise"


# ---------------------------------------------------------------------------
# 3. Parts table has rows
# ---------------------------------------------------------------------------

def test_sqlite_parts_table_populated(db: sqlite3.Connection) -> None:
    count = db.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
    assert count > 0, "parts table should have at least one row after seeding"


# ---------------------------------------------------------------------------
# 4. Compatibility indexes are present
# ---------------------------------------------------------------------------

def test_sqlite_compatibility_index_present(db: sqlite3.Connection) -> None:
    index_names = {
        row[0]
        for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
    }
    assert "idx_compat_part"  in index_names, "idx_compat_part index must exist"
    assert "idx_compat_model" in index_names, "idx_compat_model index must exist"


# ---------------------------------------------------------------------------
# 5. Chroma returns top-k results
# ---------------------------------------------------------------------------

def test_chroma_returns_top_k_docs(chroma_collection) -> None:
    results = chroma_collection.query(
        query_texts=["ice maker broken"], n_results=2
    )
    docs = results["documents"][0]
    assert len(docs) == 2, "Should return exactly n_results=2 documents"


# ---------------------------------------------------------------------------
# 6. Chroma metadata filter by appliance_type
# ---------------------------------------------------------------------------

def test_chroma_metadata_filter_by_appliance_type(chroma_collection) -> None:
    results = chroma_collection.query(
        query_texts=["not draining"],
        n_results=3,
        where={"appliance_type": "dishwasher"},
    )
    metadatas = results["metadatas"][0]
    assert len(metadatas) > 0, "Filtered query should return at least one result"
    for m in metadatas:
        assert m["appliance_type"] == "dishwasher", (
            "All returned documents must match the appliance_type filter"
        )


# ---------------------------------------------------------------------------
# 7. Foreign-key consistency — all parts reference valid category_ids
# ---------------------------------------------------------------------------

def test_category_id_foreign_keys_consistent(db: sqlite3.Connection) -> None:
    orphans = db.execute(
        """
        SELECT p.part_number
        FROM parts p
        LEFT JOIN appliance_categories ac ON ac.id = p.category_id
        WHERE ac.id IS NULL
        """
    ).fetchall()
    assert orphans == [], (
        f"Parts with invalid category_id found: {[r[0] for r in orphans]}"
    )


# ---------------------------------------------------------------------------
# 8. Washer stub category is inactive
# ---------------------------------------------------------------------------

def test_appliance_categories_stub_is_inactive(db: sqlite3.Connection) -> None:
    row = db.execute(
        "SELECT is_active FROM appliance_categories WHERE slug = 'washer'"
    ).fetchone()
    assert row is not None, "Washer category must exist in appliance_categories"
    assert row["is_active"] == 0, (
        "Washer category must have is_active = 0 (stub, not trained)"
    )
