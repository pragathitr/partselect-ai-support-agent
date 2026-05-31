"""Unit tests for the backend tool functions.

All tests use the in-memory `db` fixture and ephemeral `chroma_collection` fixture
from conftest.py — no real DB path or OpenAI calls.

conftest seed data recap:
  Parts:     PS11752778 (test fridge filter), PS11769116 (test fridge ice maker),
             PS11752078 (test dishwasher latch)
  Models:    WRF555SDFZ (fridge), WDT780SAEM1 (DW)
  Compat:    PS11752778↔WRF555SDFZ (confirmed), PS11769116↔WRF555SDFZ (confirmed),
             PS11752078↔WDT780SAEM1 (confirmed)
  Symptoms:  SY_FRIDGE_ICE_MAKER_FAIL → PS11769116 (rank 1), PS11752778 (rank 2)
             SY_DW_NOT_DRAINING → PS11752078 (rank 1)
"""
import pytest

from backend.tools.parts import (
    search_parts,
    get_part_detail,
    check_compatibility,
    get_compatible_models,
)
from backend.tools.diagnose import list_symptoms, diagnose_symptom
from backend.tools.install import get_install_guide
from backend.tools.rag import search_repair_articles
from backend.tools.orders import get_order_status


# ===========================================================================
# search_parts
# ===========================================================================

def test_search_parts_found_by_name(db):
    results = search_parts("Ice Maker", conn=db)
    assert len(results) >= 1
    part_numbers = [r["part_number"] for r in results]
    assert "PS11769116" in part_numbers


def test_search_parts_found_by_oem_number(db):
    results = search_parts("WPW10321304", conn=db)
    assert len(results) >= 1
    assert results[0]["part_number"] == "PS11752778"


def test_search_parts_appliance_type_filter(db):
    results = search_parts("filter", appliance_type="refrigerator", conn=db)
    assert len(results) >= 1
    for r in results:
        assert r["appliance_type"] == "refrigerator"


def test_search_parts_no_match_returns_empty(db):
    results = search_parts("zzznomatchxyz", conn=db)
    assert results == []


def test_search_parts_appliance_filter_excludes_other_type(db):
    results = search_parts("latch", appliance_type="refrigerator", conn=db)
    # PS11752078 is a dishwasher latch — should not appear under refrigerator filter
    part_numbers = [r["part_number"] for r in results]
    assert "PS11752078" not in part_numbers


# ===========================================================================
# get_part_detail
# ===========================================================================

def test_get_part_detail_by_ps_number(db):
    result = get_part_detail("PS11752778", conn=db)
    assert result is not None
    assert result["part_number"] == "PS11752778"
    assert result["mfr_part_number"] == "WPW10321304"
    assert result["price"] == pytest.approx(49.95)


def test_get_part_detail_by_oem_number(db):
    result = get_part_detail("WPW10321304", conn=db)
    assert result is not None
    assert result["part_number"] == "PS11752778"


def test_get_part_detail_not_found_returns_none(db):
    result = get_part_detail("PSNOTEXIST", conn=db)
    assert result is None


# ===========================================================================
# check_compatibility
# ===========================================================================

def test_check_compatibility_confirmed(db):
    result = check_compatibility("PS11752778", "WRF555SDFZ", conn=db)
    assert result["compatible"] is True
    assert result["confidence"] == "confirmed"


def test_check_compatibility_unknown_model(db):
    result = check_compatibility("PS11752778", "MODELNOTEXIST", conn=db)
    assert result["compatible"] is False
    assert result["confidence"] == "unknown"


def test_check_compatibility_incompatible_pair(db):
    # PS11752778 (fridge part) is not linked to WDT780SAEM1 (dishwasher model)
    result = check_compatibility("PS11752778", "WDT780SAEM1", conn=db)
    assert result["compatible"] is False
    assert result["confidence"] == "unknown"


# ===========================================================================
# get_compatible_models
# ===========================================================================

def test_get_compatible_models_returns_list(db):
    result = get_compatible_models("PS11752778", conn=db)
    assert isinstance(result, list)
    assert len(result) >= 1
    model_numbers = [r["model_number"] for r in result]
    assert "WRF555SDFZ" in model_numbers


def test_get_compatible_models_unknown_part_returns_empty(db):
    result = get_compatible_models("PSUNKNOWN", conn=db)
    assert result == []


# ===========================================================================
# list_symptoms
# ===========================================================================

def test_list_symptoms_refrigerator(db):
    results = list_symptoms("refrigerator", conn=db)
    assert len(results) >= 1
    ids = [r["id"] for r in results]
    assert "SY_FRIDGE_ICE_MAKER_FAIL" in ids


def test_list_symptoms_dishwasher(db):
    results = list_symptoms("dishwasher", conn=db)
    assert len(results) >= 1
    ids = [r["id"] for r in results]
    assert "SY_DW_NOT_DRAINING" in ids


def test_list_symptoms_result_shape(db):
    results = list_symptoms("refrigerator", conn=db)
    for r in results:
        assert "id" in r
        assert "description" in r
        assert "is_safety_critical" in r


def test_list_symptoms_unknown_appliance_returns_empty(db):
    results = list_symptoms("oven", conn=db)
    assert results == []


def test_list_symptoms_cross_appliance_isolation(db):
    fridge = {r["id"] for r in list_symptoms("refrigerator", conn=db)}
    dw     = {r["id"] for r in list_symptoms("dishwasher",   conn=db)}
    assert fridge.isdisjoint(dw)


# ===========================================================================
# diagnose_symptom
# ===========================================================================

def test_diagnose_symptom_no_model_filter(db):
    result = diagnose_symptom("SY_FRIDGE_ICE_MAKER_FAIL", conn=db)
    assert len(result) == 2
    part_numbers = [r["part_number"] for r in result]
    assert part_numbers[0] == "PS11769116"  # rank 1
    assert part_numbers[1] == "PS11752778"  # rank 2


def test_diagnose_symptom_with_model_filter(db):
    result = diagnose_symptom("SY_FRIDGE_ICE_MAKER_FAIL", model_number="WRF555SDFZ", conn=db)
    assert len(result) >= 1
    for r in result:
        assert "confidence" in r
        assert r["confidence"] in ("confirmed", "inferred")
    ranks = [r["rank"] for r in result]
    assert ranks == sorted(ranks)  # ordered by rank


def test_diagnose_symptom_unknown_symptom_returns_empty(db):
    result = diagnose_symptom("SY_UNKNOWN_XYZ", conn=db)
    assert result == []


# ===========================================================================
# get_install_guide
# ===========================================================================

def test_get_install_guide_has_steps(db):
    db.execute(
        "INSERT INTO install_guides VALUES (?, ?, ?, ?, ?)",
        ("PS11752778", 1, "Disconnect power to the refrigerator.", None, "Electrical hazard — unplug first."),
    )
    db.execute(
        "INSERT INTO install_guides VALUES (?, ?, ?, ?, ?)",
        ("PS11752778", 2, "Locate and remove the old filter.", None, None),
    )
    db.commit()

    result = get_install_guide("PS11752778", conn=db)
    assert len(result) == 2
    assert result[0]["step_order"] == 1
    assert result[1]["step_order"] == 2
    assert "Disconnect" in result[0]["instruction"]
    assert result[0]["safety_note"] is not None


def test_get_install_guide_no_steps_returns_empty(db):
    result = get_install_guide("PS11769116", conn=db)
    assert result == []


# ===========================================================================
# search_repair_articles
# ===========================================================================

def test_search_repair_articles_returns_results(chroma_collection):
    result = search_repair_articles("ice maker not working", collection=chroma_collection)
    assert isinstance(result, list)
    assert len(result) >= 1
    first = result[0]
    assert "id" in first
    assert "content" in first
    assert "metadata" in first


def test_search_repair_articles_appliance_type_filter(chroma_collection):
    result = search_repair_articles(
        "fix problem", appliance_type="dishwasher", collection=chroma_collection
    )
    # All returned articles must be dishwasher articles
    for r in result:
        assert r["metadata"]["appliance_type"] == "dishwasher"


def test_search_repair_articles_n_results_respected(chroma_collection):
    result = search_repair_articles("water", n_results=1, collection=chroma_collection)
    assert len(result) == 1


def test_search_repair_articles_empty_collection_returns_empty():
    import chromadb
    import uuid
    from backend.tests.conftest import _MockEmbedding

    client = chromadb.EphemeralClient()
    empty_col = client.create_collection(
        name=f"empty_{uuid.uuid4().hex[:8]}",
        embedding_function=_MockEmbedding(),
    )
    result = search_repair_articles("anything", collection=empty_col)
    assert result == []


# ===========================================================================
# get_order_status
# ===========================================================================

def test_get_order_status_found(db):
    db.execute(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",
        ("ORD-TEST-001", "PS11752778", "shipped", "1Z999AA10123456784", "2026-06-03", "demo@example.com"),
    )
    db.commit()

    result = get_order_status("ORD-TEST-001", "demo@example.com", conn=db)
    assert result is not None
    assert result["order_id"] == "ORD-TEST-001"
    assert result["status"] == "shipped"
    assert result["tracking_number"] == "1Z999AA10123456784"


def test_get_order_status_not_found_returns_none(db):
    result = get_order_status("ORD-DOESNOTEXIST", "demo@example.com", conn=db)
    assert result is None


def test_get_order_status_wrong_email_returns_none(db):
    db.execute(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",
        ("ORD-TEST-002", "PS11752778", "shipped", "1Z999AA10123456784", "2026-06-03", "demo@example.com"),
    )
    db.commit()

    result = get_order_status("ORD-TEST-002", "wrong@example.com", conn=db)
    assert result is None
