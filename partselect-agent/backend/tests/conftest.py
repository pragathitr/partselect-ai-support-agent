"""Shared pytest fixtures for the data layer and tool tests."""
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Generator

import chromadb
import pytest
from dotenv import load_dotenv

# Load .env so LLM clients can be instantiated during collection.
# Fall back to dummy values so tests pass in CI without real keys —
# all LLM calls are mocked in the test suite anyway.
load_dotenv()
os.environ.setdefault("OPENAI_API_KEY", "sk-openai-test-dummy")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-dummy")
os.environ.setdefault("GOOGLE_API_KEY", "gemini-test-dummy")


# ---------------------------------------------------------------------------
# SQLite fixture — in-memory DB with schema + minimal seed data
# ---------------------------------------------------------------------------

SCHEMA_PATH = Path(__file__).parent.parent / "data" / "schema.sql"


@pytest.fixture
def db() -> Generator[sqlite3.Connection, None, None]:
    """In-memory SQLite database with schema applied and minimal seed data."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text())

    conn.executemany(
        "INSERT INTO appliance_categories VALUES (?,?,?,?,?)",
        [
            (1, "refrigerator", "Refrigerator", "config/specialists/refrigerator.yaml", 1),
            (2, "dishwasher",   "Dishwasher",   "config/specialists/dishwasher.yaml",   1),
            (3, "washer",       "Washer",        "config/specialists/washer.yaml",        0),
        ],
    )
    conn.executemany(
        "INSERT INTO parts VALUES (?,?,?,?,?,?,?,?,?)",
        [
            ("PS11752778", "EveryDrop Water Filter 3", 1, "Whirlpool", 49.95,
             "OEM water filter for Whirlpool refrigerators.", 1, None, "WPW10321304"),
            ("PS11769116", "Refrigerator Ice Maker Assembly", 1, "Whirlpool", 89.99,
             "Complete ice maker assembly.", 1, None, "W10377151"),
            ("PS11752078", "Dishwasher Door Latch Assembly", 2, "Whirlpool", 24.99,
             "Door latch for Whirlpool dishwashers.", 1, None, "WPW10482502"),
        ],
    )
    conn.executemany(
        "INSERT INTO models VALUES (?,?,?,?)",
        [
            ("WRF555SDFZ",  "Whirlpool", 1, "Whirlpool 25 cu ft French Door Refrigerator"),
            ("WDT780SAEM1", "Whirlpool", 2, "Whirlpool 24 in Built-In Dishwasher"),
        ],
    )
    conn.executemany(
        "INSERT INTO compatibility VALUES (?,?,?)",
        [
            ("PS11752778", "WRF555SDFZ",  "confirmed"),
            ("PS11769116", "WRF555SDFZ",  "confirmed"),
            ("PS11752078", "WDT780SAEM1", "confirmed"),
        ],
    )
    conn.executemany(
        "INSERT INTO symptoms VALUES (?,?,?,?)",
        [
            ("SY_FRIDGE_ICE_MAKER_FAIL", "Ice maker not producing ice",  1, 0),
            ("SY_DW_NOT_DRAINING",       "Dishwasher not draining",      2, 0),
        ],
    )
    conn.executemany(
        "INSERT INTO symptom_fixes VALUES (?,?,?)",
        [
            ("SY_FRIDGE_ICE_MAKER_FAIL", "PS11769116", 1),
            ("SY_FRIDGE_ICE_MAKER_FAIL", "PS11752778", 2),
            ("SY_DW_NOT_DRAINING",       "PS11752078", 1),
        ],
    )
    conn.commit()
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Chroma fixture — ephemeral (in-memory) client with mock embedding function
# Zero real API calls, deterministic output.
# ---------------------------------------------------------------------------

class _MockEmbedding(chromadb.EmbeddingFunction):
    """Returns deterministic fake embeddings — no OpenAI call."""

    def __init__(self) -> None:
        pass

    def name(self) -> str:
        return "mock_embedding"

    def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
        # Non-zero distinct vectors so cosine similarity is meaningful
        return [[float(i + 1) * 0.01] * 1536 for i, _ in enumerate(input)]


@pytest.fixture
def chroma_collection() -> chromadb.Collection:
    """Ephemeral Chroma collection with mock embeddings and sample repair articles.

    Uses a unique collection name per test run to avoid cross-test collisions
    when EphemeralClient shares in-process state (chromadb >= 1.x behaviour).
    """
    client = chromadb.EphemeralClient()
    # Unique name prevents 'already exists' errors when EphemeralClient
    # reuses its in-process instance across fixtures in the same session.
    unique_name = f"test_repair_{uuid.uuid4().hex[:8]}"
    collection = client.create_collection(
        name=unique_name,
        embedding_function=_MockEmbedding(),
    )
    collection.add(
        documents=[
            "How to fix ice maker not working on Whirlpool refrigerator",
            "Water filter replacement guide for Whirlpool refrigerators",
            "Dishwasher not draining — step by step fix",
        ],
        metadatas=[
            {"appliance_type": "refrigerator", "symptom": "ice_maker_fail"},
            {"appliance_type": "refrigerator", "symptom": "water_filter"},
            {"appliance_type": "dishwasher",   "symptom": "not_draining"},
        ],
        ids=["A01", "A02", "A03"],
    )
    return collection
