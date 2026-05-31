"""
Graph routing + node behavior unit tests.

Covers:
  OOS routing      — supervisor → decline (bypasses specialist + validator)
  In-scope routing — supervisor → specialist → validator
  Validator verdicts — pass, warn, escalate
  Supervisor exception fallback
  run_agent() state contract
  Multi-turn history preservation

All LLM calls mocked by patching the module-level names in backend.agent.nodes.
RunnableSequence objects are Pydantic v2 models and block mocker.patch.object,
so we replace the entire binding with mocker.patch("backend.agent.nodes.<name>").
"""
from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from backend.agent import run_agent
from backend.agent.nodes import _SupervisorDecision, _ValidatorOutput


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sup(appliance_type="refrigerator", model_number=None, oos=False):
    return _SupervisorDecision(
        appliance_type=appliance_type,
        model_number=model_number,
        is_out_of_scope=oos,
    )


def _val(verdict="pass", feedback="Looks good."):
    return _ValidatorOutput(verdict=verdict, feedback=feedback)


def _patch(mocker, *, supervisor=None, specialist_content=None, validator=None):
    """Patch all three module-level LLM chains in backend.agent.nodes.

    Returns a dict of mocks so callers can assert call counts / spies.
    """
    m_sup = mocker.patch("backend.agent.nodes._structured_supervisor")
    if supervisor is not None:
        m_sup.invoke.return_value = supervisor

    m_spec = mocker.patch("backend.agent.nodes._specialist_with_tools")
    if specialist_content is not None:
        m_spec.invoke.return_value = AIMessage(content=specialist_content)

    m_val = mocker.patch("backend.agent.nodes._structured_validator")
    if validator is not None:
        m_val.invoke.return_value = validator

    return {"supervisor": m_sup, "specialist": m_spec, "validator": m_val}


# ---------------------------------------------------------------------------
# OOS routing
# ---------------------------------------------------------------------------


def test_oos_sets_pass_verdict(mocker):
    """decline_node sets validator_verdict='pass' without running the real validator."""
    _patch(mocker, supervisor=_sup(appliance_type="unknown", oos=True))
    result = run_agent("How do I fix my washing machine?")
    assert result["validator_verdict"] == "pass"


def test_oos_does_not_call_specialist(mocker):
    """Specialist must never be invoked for out-of-scope questions."""
    mocks = _patch(mocker, supervisor=_sup(appliance_type="unknown", oos=True))
    run_agent("What's the best oven for baking?")
    mocks["specialist"].invoke.assert_not_called()


def test_oos_does_not_call_validator(mocker):
    """Validator must never be invoked for out-of-scope questions."""
    mocks = _patch(mocker, supervisor=_sup(appliance_type="unknown", oos=True))
    run_agent("How do I clean my HVAC filter?")
    mocks["validator"].invoke.assert_not_called()


def test_oos_last_message_mentions_supported_appliances(mocker):
    """Decline response must redirect the customer to refrigerator / dishwasher scope."""
    _patch(mocker, supervisor=_sup(appliance_type="unknown", oos=True))
    result = run_agent("Can you recommend a vacuum cleaner?")
    last_msg = result["messages"][-1]
    assert isinstance(last_msg, AIMessage)
    content = last_msg.content.lower()
    assert "refrigerator" in content or "dishwasher" in content


def test_oos_last_message_contains_support_number(mocker):
    """Decline response must include the PartSelect support phone number."""
    _patch(mocker, supervisor=_sup(appliance_type="unknown", oos=True))
    result = run_agent("I need help with my dryer.")
    assert "1-888-738-4871" in result["messages"][-1].content


# ---------------------------------------------------------------------------
# In-scope routing
# ---------------------------------------------------------------------------


def test_in_scope_refrigerator_calls_specialist(mocker):
    mocks = _patch(
        mocker,
        supervisor=_sup(appliance_type="refrigerator"),
        specialist_content="Here is info about your fridge.",
        validator=_val("pass"),
    )
    run_agent("My fridge is leaking.")
    mocks["specialist"].invoke.assert_called_once()


def test_in_scope_dishwasher_calls_specialist(mocker):
    mocks = _patch(
        mocker,
        supervisor=_sup(appliance_type="dishwasher"),
        specialist_content="Dishwasher drain info.",
        validator=_val("pass"),
    )
    run_agent("My dishwasher is not draining.")
    mocks["specialist"].invoke.assert_called_once()


def test_in_scope_appliance_type_and_model_in_state(mocker):
    _patch(
        mocker,
        supervisor=_sup(appliance_type="refrigerator", model_number="WRF555SDFZ"),
        specialist_content="PS11752778 is the water filter you need.",
        validator=_val("pass"),
    )
    result = run_agent("What water filter do I need for WRF555SDFZ?")
    assert result["appliance_type"] == "refrigerator"
    assert result["model_number"] == "WRF555SDFZ"


# ---------------------------------------------------------------------------
# Validator verdicts
# ---------------------------------------------------------------------------


def test_validator_pass_verdict_and_feedback_in_state(mocker):
    _patch(
        mocker,
        supervisor=_sup(),
        specialist_content="PS11752778 fits WRF555SDFZ — confirmed compatible.",
        validator=_val("pass", "Accurate — part number and compatibility confirmed."),
    )
    result = run_agent("Is PS11752778 compatible with WRF555SDFZ?")
    assert result["validator_verdict"] == "pass"
    assert "Accurate" in result["validator_feedback"]


def test_validator_warn_verdict_preserved(mocker):
    _patch(
        mocker,
        supervisor=_sup(),
        specialist_content="The part might work for your fridge.",
        validator=_val("warn", "Vague — no specific part number cited."),
    )
    result = run_agent("What part do I need for my fridge?")
    assert result["validator_verdict"] == "warn"
    assert "Vague" in result["validator_feedback"]


def test_validator_escalate_verdict_in_state(mocker):
    _patch(
        mocker,
        supervisor=_sup(appliance_type="refrigerator"),
        specialist_content="You may have a refrigerant leak.",
        validator=_val("escalate", "Safety hazard — potential gas leak."),
    )
    result = run_agent("I smell gas from my refrigerator.")
    assert result["validator_verdict"] == "escalate"


def test_validator_escalate_replaces_specialist_response(mocker):
    """When verdict is 'escalate', the final message must be the escalation template."""
    _patch(
        mocker,
        supervisor=_sup(appliance_type="refrigerator"),
        specialist_content="Try adjusting the compressor.",
        validator=_val("escalate", "Electrical hazard."),
    )
    result = run_agent("My refrigerator is sparking and smoking.")
    last_msg = result["messages"][-1]
    assert isinstance(last_msg, AIMessage)
    content = last_msg.content
    assert "1-888-738-4871" in content or "technician" in content.lower()


# ---------------------------------------------------------------------------
# Supervisor exception fallback
# ---------------------------------------------------------------------------


def test_supervisor_exception_falls_back_to_in_scope(mocker):
    """When the supervisor LLM raises, the fallback sets appliance_type='unknown'
    and is_out_of_scope=False so the graph continues to the specialist."""
    mocks = _patch(
        mocker,
        specialist_content="How can I help you?",
        validator=_val("pass"),
    )
    mocks["supervisor"].invoke.side_effect = RuntimeError("LLM timeout")

    result = run_agent("My fridge is leaking water.")
    assert result["appliance_type"] == "unknown"
    assert not result.get("is_out_of_scope")


# ---------------------------------------------------------------------------
# State contract
# ---------------------------------------------------------------------------


def test_run_agent_has_all_required_state_keys(mocker):
    _patch(
        mocker,
        supervisor=_sup(),
        specialist_content="Here is your answer.",
        validator=_val("pass"),
    )
    result = run_agent("What water filter fits my Whirlpool?")
    for key in ("messages", "appliance_type", "model_number", "validator_verdict", "validator_feedback"):
        assert key in result, f"Missing required state key: {key}"


def test_run_agent_messages_include_human_turn(mocker):
    _patch(
        mocker,
        supervisor=_sup(),
        specialist_content="Here is your answer.",
        validator=_val("pass"),
    )
    result = run_agent("Tell me about water filters for my fridge.")
    human_msgs = [m for m in result["messages"] if isinstance(m, HumanMessage)]
    assert len(human_msgs) >= 1
    assert any("water filter" in m.content.lower() for m in human_msgs)


# ---------------------------------------------------------------------------
# Multi-turn history
# ---------------------------------------------------------------------------


def test_multi_turn_history_preserved_in_messages(mocker):
    """Prior conversation messages must appear in the final state after a new turn."""
    _patch(
        mocker,
        supervisor=_sup(appliance_type="refrigerator", model_number="WRF555SDFZ"),
        specialist_content="The filter you need is PS11752778.",
        validator=_val("pass"),
    )
    history = [
        HumanMessage(content="My fridge model is WRF555SDFZ."),
        AIMessage(content="Got it — I will keep that in mind."),
    ]
    result = run_agent("What water filter do I need?", history=history)

    all_contents = [
        m.content for m in result["messages"]
        if isinstance(m, (HumanMessage, AIMessage)) and isinstance(m.content, str)
    ]
    assert any("WRF555SDFZ" in c for c in all_contents), "Prior model number must be in message history"
    assert any("water filter" in c.lower() for c in all_contents), "New question must be in messages"
