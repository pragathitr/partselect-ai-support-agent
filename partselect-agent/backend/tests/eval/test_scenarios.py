"""
Eval suite — 25 parameterized scenarios.

Coverage matrix:
  OOS (7)           — wrong appliance type, completely off-topic, small talk
  Refrigerator (5)  — parts lookup, compatibility, install, troubleshooting
  Dishwasher (5)    — parts lookup, compatibility, install, troubleshooting
  Compatibility (3) — cross-checks for both appliance types
  Order tracking (2) — known order ID, vague order query
  Safety escalation (3) — gas, electrical, flooding

All LLM calls mocked by replacing module-level names via mocker.patch().
RunnableSequence (Pydantic v2) blocks setattr, so we patch the module binding,
not an attribute on the object.
"""
from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage

from backend.agent import run_agent
from backend.agent.nodes import _SupervisorDecision, _ValidatorOutput


# ---------------------------------------------------------------------------
# Scenario definitions
#
# Keys:
#   id                   — unique test ID shown in pytest -v output
#   question             — customer message passed to run_agent()
#   supervisor_appliance — appliance_type returned by the mocked supervisor
#   supervisor_model     — model_number returned (or None)
#   supervisor_oos       — is_out_of_scope flag (True → decline path)
#   specialist_content   — AIMessage.content for in-scope tests (None for OOS)
#   validator_verdict    — verdict returned by mocked validator (None for OOS)
#   validator_feedback   — feedback string (None for OOS)
#   expect_decline       — True → assert decline redirect in last message
#   expect_verdict       — expected validator_verdict in final state
#   expect_appliance     — expected appliance_type, or None to skip check
# ---------------------------------------------------------------------------

SCENARIOS: list[dict] = [
    # -----------------------------------------------------------------------
    # Out of scope (7)
    # -----------------------------------------------------------------------
    {
        "id": "oos_washing_machine",
        "question": "How do I fix my washing machine that won't spin?",
        "supervisor_appliance": "unknown",
        "supervisor_model": None,
        "supervisor_oos": True,
        "specialist_content": None,
        "validator_verdict": None,
        "validator_feedback": None,
        "expect_decline": True,
        "expect_verdict": "pass",
        "expect_appliance": None,
    },
    {
        "id": "oos_oven",
        "question": "What's the best oven for baking bread at high altitude?",
        "supervisor_appliance": "unknown",
        "supervisor_model": None,
        "supervisor_oos": True,
        "specialist_content": None,
        "validator_verdict": None,
        "validator_feedback": None,
        "expect_decline": True,
        "expect_verdict": "pass",
        "expect_appliance": None,
    },
    {
        "id": "oos_hvac",
        "question": "How do I clean my HVAC air filter?",
        "supervisor_appliance": "unknown",
        "supervisor_model": None,
        "supervisor_oos": True,
        "specialist_content": None,
        "validator_verdict": None,
        "validator_feedback": None,
        "expect_decline": True,
        "expect_verdict": "pass",
        "expect_appliance": None,
    },
    {
        "id": "oos_weather",
        "question": "What's the weather like in New York today?",
        "supervisor_appliance": "unknown",
        "supervisor_model": None,
        "supervisor_oos": True,
        "specialist_content": None,
        "validator_verdict": None,
        "validator_feedback": None,
        "expect_decline": True,
        "expect_verdict": "pass",
        "expect_appliance": None,
    },
    {
        "id": "oos_microwave",
        "question": "My microwave is sparking inside — is this dangerous?",
        "supervisor_appliance": "unknown",
        "supervisor_model": None,
        "supervisor_oos": True,
        "specialist_content": None,
        "validator_verdict": None,
        "validator_feedback": None,
        "expect_decline": True,
        "expect_verdict": "pass",
        "expect_appliance": None,
    },
    {
        "id": "oos_vacuum",
        "question": "Can you recommend a good robot vacuum cleaner?",
        "supervisor_appliance": "unknown",
        "supervisor_model": None,
        "supervisor_oos": True,
        "specialist_content": None,
        "validator_verdict": None,
        "validator_feedback": None,
        "expect_decline": True,
        "expect_verdict": "pass",
        "expect_appliance": None,
    },
    {
        "id": "oos_small_talk",
        "question": "Hello! How are you today?",
        "supervisor_appliance": "unknown",
        "supervisor_model": None,
        "supervisor_oos": True,
        "specialist_content": None,
        "validator_verdict": None,
        "validator_feedback": None,
        "expect_decline": True,
        "expect_verdict": "pass",
        "expect_appliance": None,
    },

    # -----------------------------------------------------------------------
    # Refrigerator (5)
    # -----------------------------------------------------------------------
    {
        "id": "fridge_ice_maker_fail",
        "question": "My Whirlpool WRF555SDFZ ice maker isn't producing ice.",
        "supervisor_appliance": "refrigerator",
        "supervisor_model": "WRF555SDFZ",
        "supervisor_oos": False,
        "specialist_content": (
            "For a Whirlpool WRF555SDFZ ice maker not producing ice, "
            "the most likely fix is replacing the Ice Maker Assembly (PS11752391, $129.28). "
            "Also check the water inlet valve (PS11775241) and water filter (PS11701542) "
            "because restricted water flow can stop ice production."
        ),
        "validator_verdict": "pass",
        "validator_feedback": "Accurate — correct part numbers cited for the reported model.",
        "expect_decline": False,
        "expect_verdict": "pass",
        "expect_appliance": "refrigerator",
    },
    {
        "id": "fridge_water_filter",
        "question": "What water filter do I need for my Whirlpool refrigerator?",
        "supervisor_appliance": "refrigerator",
        "supervisor_model": None,
        "supervisor_oos": False,
        "specialist_content": (
            "For many Whirlpool French Door refrigerators, the EveryDrop Water & Ice Filter 1 "
            "(PS11701542, $54.99) is the matching filter. Please share your model number "
            "so I can confirm compatibility."
        ),
        "validator_verdict": "pass",
        "validator_feedback": "Accurate product recommendation with price.",
        "expect_decline": False,
        "expect_verdict": "pass",
        "expect_appliance": "refrigerator",
    },
    {
        "id": "fridge_ice_maker_install",
        "question": "How do I replace the ice maker on my Whirlpool refrigerator?",
        "supervisor_appliance": "refrigerator",
        "supervisor_model": None,
        "supervisor_oos": False,
        "specialist_content": (
            "To replace the ice maker: "
            "1. Unplug the refrigerator. "
            "2. Remove the ice bin and old assembly. "
            "3. Disconnect the wire harness. "
            "4. Install the new assembly (PS11752391) and reconnect."
        ),
        "validator_verdict": "pass",
        "validator_feedback": "Clear installation steps with safety precautions.",
        "expect_decline": False,
        "expect_verdict": "pass",
        "expect_appliance": "refrigerator",
    },
    {
        "id": "fridge_compat_check",
        "question": "Is part PS11752778 compatible with my Whirlpool WRF555SDFZ?",
        "supervisor_appliance": "refrigerator",
        "supervisor_model": "WRF555SDFZ",
        "supervisor_oos": False,
        "specialist_content": (
            "No — PS11752778 is a Refrigerator Door Shelf Bin and is not listed as compatible "
            "with the Whirlpool WRF555SDFZ in the seeded catalog."
        ),
        "validator_verdict": "pass",
        "validator_feedback": "Compatibility confirmed with correct confidence level.",
        "expect_decline": False,
        "expect_verdict": "pass",
        "expect_appliance": "refrigerator",
    },
    {
        "id": "fridge_not_cooling",
        "question": "My refrigerator is not cooling at all — what part could be failing?",
        "supervisor_appliance": "refrigerator",
        "supervisor_model": None,
        "supervisor_oos": False,
        "specialist_content": (
            "A refrigerator that is not cooling at all is usually caused by "
            "a failed evaporator fan motor, a faulty start relay, or a bad compressor. "
            "Please share your model number so I can identify the exact part."
        ),
        "validator_verdict": "warn",
        "validator_feedback": "Helpful but vague — no part numbers cited without model number.",
        "expect_decline": False,
        "expect_verdict": "warn",
        "expect_appliance": "refrigerator",
    },

    # -----------------------------------------------------------------------
    # Dishwasher (5)
    # -----------------------------------------------------------------------
    {
        "id": "dw_not_draining",
        "question": "My Whirlpool WDT780SAEM1 dishwasher is not draining after the cycle.",
        "supervisor_appliance": "dishwasher",
        "supervisor_model": "WDT780SAEM1",
        "supervisor_oos": False,
        "specialist_content": (
            "For a WDT780SAEM1 not draining, the drain pump assembly is the most common cause. "
            "Also check if the drain hose is kinked or the filter is clogged."
        ),
        "validator_verdict": "pass",
        "validator_feedback": "Accurate diagnosis with correct model reference.",
        "expect_decline": False,
        "expect_verdict": "pass",
        "expect_appliance": "dishwasher",
    },
    {
        "id": "dw_door_latch",
        "question": "I need a new door latch for my Whirlpool dishwasher.",
        "supervisor_appliance": "dishwasher",
        "supervisor_model": None,
        "supervisor_oos": False,
        "specialist_content": (
            "The Dishwasher Door Latch - Black (PS11756967) is $31.18 and in stock. "
            "It is confirmed compatible with the Whirlpool WDT780SAEM1."
        ),
        "validator_verdict": "pass",
        "validator_feedback": "Accurate part recommendation with price and stock status.",
        "expect_decline": False,
        "expect_verdict": "pass",
        "expect_appliance": "dishwasher",
    },
    {
        "id": "dw_install_latch",
        "question": "How do I install the door latch assembly PS11756967?",
        "supervisor_appliance": "dishwasher",
        "supervisor_model": None,
        "supervisor_oos": False,
        "specialist_content": (
            "To install PS11756967: "
            "1. Disconnect power to the dishwasher. "
            "2. Open the door and remove the inner door panel screws. "
            "3. Lift out the old latch assembly and snap in the new one. "
            "4. Reassemble and restore power."
        ),
        "validator_verdict": "pass",
        "validator_feedback": "Clear step-by-step with safety first.",
        "expect_decline": False,
        "expect_verdict": "pass",
        "expect_appliance": "dishwasher",
    },
    {
        "id": "dw_compat_latch_model",
        "question": "Is dishwasher part PS11756967 compatible with the Whirlpool WDT780SAEM1?",
        "supervisor_appliance": "dishwasher",
        "supervisor_model": "WDT780SAEM1",
        "supervisor_oos": False,
        "specialist_content": (
            "Yes — PS11756967 (Dishwasher Door Latch - Black) is confirmed compatible "
            "with the Whirlpool WDT780SAEM1."
        ),
        "validator_verdict": "pass",
        "validator_feedback": "Compatibility confirmed.",
        "expect_decline": False,
        "expect_verdict": "pass",
        "expect_appliance": "dishwasher",
    },
    {
        "id": "dw_white_residue",
        "question": "My dishwasher leaves white spots and residue on dishes after washing.",
        "supervisor_appliance": "dishwasher",
        "supervisor_model": None,
        "supervisor_oos": False,
        "specialist_content": (
            "White residue is usually caused by hard water deposits. "
            "Check whether your rinse aid dispenser is empty and refill it. "
            "If the problem persists, the dispenser assembly may need replacement."
        ),
        "validator_verdict": "pass",
        "validator_feedback": "Helpful troubleshooting with actionable steps.",
        "expect_decline": False,
        "expect_verdict": "pass",
        "expect_appliance": "dishwasher",
    },

    # -----------------------------------------------------------------------
    # Compatibility (3)
    # -----------------------------------------------------------------------
    {
        "id": "compat_models_for_filter",
        "question": "What refrigerator models is part PS11752778 compatible with?",
        "supervisor_appliance": "refrigerator",
        "supervisor_model": None,
        "supervisor_oos": False,
        "specialist_content": (
            "PS11752778 (Refrigerator Door Shelf Bin) is compatible with side-by-side "
            "Whirlpool models including WRS325FDAM04, WRS322FDAW03, and WRS315SDHM01."
        ),
        "validator_verdict": "pass",
        "validator_feedback": "Accurate compatibility list.",
        "expect_decline": False,
        "expect_verdict": "pass",
        "expect_appliance": "refrigerator",
    },
    {
        "id": "compat_dw_latch_explicit",
        "question": "Does dishwasher part PS11756967 fit Whirlpool model WDT780SAEM1?",
        "supervisor_appliance": "dishwasher",
        "supervisor_model": "WDT780SAEM1",
        "supervisor_oos": False,
        "specialist_content": (
            "PS11756967 is confirmed compatible with the Whirlpool WDT780SAEM1."
        ),
        "validator_verdict": "pass",
        "validator_feedback": "Correct — confirmed compatibility.",
        "expect_decline": False,
        "expect_verdict": "pass",
        "expect_appliance": "dishwasher",
    },
    {
        "id": "compat_filter_oem_number",
        "question": "Does OEM filter WPW10321304 work with my Whirlpool WRF555SDFZ fridge?",
        "supervisor_appliance": "refrigerator",
        "supervisor_model": "WRF555SDFZ",
        "supervisor_oos": False,
        "specialist_content": (
            "WPW10321304 is the OEM number for PS11752778, the Refrigerator Door Shelf Bin. "
            "It is not listed as compatible with the Whirlpool WRF555SDFZ in the seeded catalog."
        ),
        "validator_verdict": "pass",
        "validator_feedback": "Correct OEM cross-reference with confirmed compatibility.",
        "expect_decline": False,
        "expect_verdict": "pass",
        "expect_appliance": "refrigerator",
    },

    # -----------------------------------------------------------------------
    # Order tracking (2)
    # -----------------------------------------------------------------------
    {
        "id": "order_tracking_known_id",
        "question": "What is the status of my order 12345?",
        "supervisor_appliance": "unknown",
        "supervisor_model": None,
        "supervisor_oos": False,
        "specialist_content": (
            "Order 12345 is currently shipped. "
            "Tracking number: 1Z999AA10123456784. "
            "Estimated delivery: 2026-06-03."
        ),
        "validator_verdict": "pass",
        "validator_feedback": "Accurate order status with tracking details.",
        "expect_decline": False,
        "expect_verdict": "pass",
        "expect_appliance": None,
    },
    {
        "id": "order_tracking_vague",
        "question": "Can you track my recent dishwasher part order?",
        "supervisor_appliance": "dishwasher",
        "supervisor_model": None,
        "supervisor_oos": False,
        "specialist_content": (
            "I'd be happy to track your order! Please provide your order ID "
            "and I'll look it up for you."
        ),
        "validator_verdict": "pass",
        "validator_feedback": "Appropriate clarification request for missing order ID.",
        "expect_decline": False,
        "expect_verdict": "pass",
        "expect_appliance": None,
    },

    # -----------------------------------------------------------------------
    # Safety escalation (3)
    # -----------------------------------------------------------------------
    {
        "id": "escalate_gas_smell",
        "question": "I smell gas coming from behind my refrigerator — what should I do?",
        "supervisor_appliance": "refrigerator",
        "supervisor_model": None,
        "supervisor_oos": False,
        "specialist_content": (
            "A gas smell near a refrigerator may indicate a refrigerant leak, "
            "which can be hazardous."
        ),
        "validator_verdict": "escalate",
        "validator_feedback": "Safety hazard — potential refrigerant/gas leak near appliance.",
        "expect_decline": False,
        "expect_verdict": "escalate",
        "expect_appliance": "refrigerator",
    },
    {
        "id": "escalate_sparking_refrigerator",
        "question": "My refrigerator is sparking and making a burning smell when I plug it in.",
        "supervisor_appliance": "refrigerator",
        "supervisor_model": None,
        "supervisor_oos": False,
        "specialist_content": (
            "Sparking at power-up can indicate a failed compressor or wiring fault."
        ),
        "validator_verdict": "escalate",
        "validator_feedback": "Electrical hazard — customer must not operate the appliance.",
        "expect_decline": False,
        "expect_verdict": "escalate",
        "expect_appliance": "refrigerator",
    },
    {
        "id": "escalate_dishwasher_flooding",
        "question": "Water is flooding out of the bottom of my dishwasher onto the kitchen floor.",
        "supervisor_appliance": "dishwasher",
        "supervisor_model": None,
        "supervisor_oos": False,
        "specialist_content": (
            "Flooding from a dishwasher can be caused by a failed door seal or pump."
        ),
        "validator_verdict": "escalate",
        "validator_feedback": "Flooding risk — customer needs immediate professional assistance.",
        "expect_decline": False,
        "expect_verdict": "escalate",
        "expect_appliance": "dishwasher",
    },
]

assert len(SCENARIOS) == 25, f"Expected 25 scenarios, got {len(SCENARIOS)}"


# ---------------------------------------------------------------------------
# Parametrized test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_scenario(mocker, sc: dict) -> None:
    # Mock supervisor (always required)
    mock_sup = mocker.patch("backend.agent.nodes._structured_supervisor")
    mock_sup.invoke.return_value = _SupervisorDecision(
        appliance_type=sc["supervisor_appliance"],
        model_number=sc["supervisor_model"],
        is_out_of_scope=sc["supervisor_oos"],
    )

    # Mock specialist + validator only for in-scope scenarios
    if not sc["expect_decline"]:
        mock_spec = mocker.patch("backend.agent.nodes._specialist_with_tools")
        mock_spec.invoke.return_value = AIMessage(content=sc["specialist_content"])

        mock_val = mocker.patch("backend.agent.nodes._structured_validator")
        mock_val.invoke.return_value = _ValidatorOutput(
            verdict=sc["validator_verdict"],
            feedback=sc["validator_feedback"] or "",
        )

    # Run the full graph
    result = run_agent(sc["question"])

    # --- Core assertions ---------------------------------------------------

    assert result["validator_verdict"] == sc["expect_verdict"], (
        f"[{sc['id']}] verdict mismatch: "
        f"got {result['validator_verdict']!r}, expected {sc['expect_verdict']!r}"
    )

    if sc["expect_appliance"]:
        assert result["appliance_type"] == sc["expect_appliance"], (
            f"[{sc['id']}] appliance_type mismatch: "
            f"got {result['appliance_type']!r}, expected {sc['expect_appliance']!r}"
        )

    last_msg = result["messages"][-1]
    assert isinstance(last_msg, AIMessage), (
        f"[{sc['id']}] last message must be AIMessage, got {type(last_msg).__name__}"
    )

    # OOS: decline message must reference the supported appliances
    if sc["expect_decline"]:
        content = last_msg.content.lower()
        assert "refrigerator" in content or "dishwasher" in content, (
            f"[{sc['id']}] decline message must mention refrigerator or dishwasher"
        )

    # Escalation: override message must include safety redirect language
    if sc["expect_verdict"] == "escalate":
        content = last_msg.content
        assert (
            "1-888-738-4871" in content
            or "technician" in content.lower()
            or "stop" in content.lower()
        ), (
            f"[{sc['id']}] escalation message must contain safety redirect"
        )
