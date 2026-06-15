"""
LangGraph node functions: supervisor, specialist, validator.

Current providers (swap to Gemini block below if preferred):
  Supervisor  — Claude Haiku  (ANTHROPIC_API_KEY)
  Specialist  — Claude Sonnet (ANTHROPIC_API_KEY)
  Validator   — GPT-4o-mini   (OPENAI_API_KEY)

Gemini alternatives are commented out below — Instalily is Google/DeepMind aligned.
To switch, comment out the "Active models" block and uncomment "Gemini models".
Requires GOOGLE_API_KEY in .env and: pip install langchain-google-genai
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Literal, Optional

import yaml
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, create_model

from backend.tools._connection import get_connection

from .state import AgentState
from .tools_schema import ALL_TOOLS

# ---------------------------------------------------------------------------
# Active models — Anthropic + OpenAI
# ---------------------------------------------------------------------------

_haiku = ChatAnthropic(
    model=os.getenv("ANTHROPIC_SUPERVISOR_MODEL", "claude-haiku-4-5-20251001"),
    temperature=0,
)
_sonnet = ChatAnthropic(
    model=os.getenv("ANTHROPIC_SPECIALIST_MODEL", "claude-sonnet-4-6"),
    temperature=0,
)
_gpt4o_mini = ChatOpenAI(
    model=os.getenv("OPENAI_VALIDATOR_MODEL", "gpt-4o-mini"),
    temperature=0,
)

_supervisor_model = _haiku
_validator_model = _gpt4o_mini
_specialist_with_tools = _sonnet.bind_tools(ALL_TOOLS)

# ---------------------------------------------------------------------------
# Gemini models — uncomment and swap above assignments to use instead
# ---------------------------------------------------------------------------
# from langchain_google_genai import ChatGoogleGenerativeAI
#
# _flash = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
# _pro   = ChatGoogleGenerativeAI(model="gemini-2.5-pro",   temperature=1)
#
# _supervisor_model      = _flash
# _validator_model       = _flash
# _specialist_with_tools = _pro.bind_tools(ALL_TOOLS)

# ---------------------------------------------------------------------------
# Specialist YAML configs
# ---------------------------------------------------------------------------

_CONFIG_DIR = Path(__file__).parent.parent / "config" / "specialists"


def _fetch_active_slugs() -> list[str]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT slug FROM appliance_categories WHERE is_active = 1 ORDER BY id"
        ).fetchall()
        return [row["slug"] for row in rows]
    except Exception:
        return ["refrigerator", "dishwasher"]
    finally:
        conn.close()


_ACTIVE_SLUGS: list[str] = _fetch_active_slugs()


def _build_fallback_prompt(slugs: list[str]) -> str:
    appliance_list = " and ".join(slugs)
    return (
        f"You are a helpful appliance parts specialist at PartSelect. "
        f"You assist with {appliance_list} parts ONLY — "
        "finding parts, checking compatibility, troubleshooting symptoms, "
        "installation guides, and order tracking. "
        f"If the customer's question is not about {appliance_list}, "
        "politely decline and direct them to partselect.com or 1-888-738-4871. "
        "Always use the available tools to look up accurate part numbers and "
        "compatibility — never guess or invent part information."
    )


_FALLBACK_SYSTEM_PROMPT = _build_fallback_prompt(_ACTIVE_SLUGS)


def _load_specialist_config(appliance_type: Optional[str]) -> dict:
    if appliance_type and appliance_type != "unknown":
        path = _CONFIG_DIR / f"{appliance_type}.yaml"
        if path.exists():
            return yaml.safe_load(path.read_text(encoding="utf-8"))
    return {"system_prompt_context": _FALLBACK_SYSTEM_PROMPT}


# ---------------------------------------------------------------------------
# Supervisor node
# ---------------------------------------------------------------------------

def _build_supervisor_system(slugs: list[str]) -> str:
    quoted = ", ".join(f"'{s}'" for s in slugs)
    appliance_list = " and ".join(slugs)
    appliance_or_list = " or ".join(
        s.capitalize() if i == 0 else s for i, s in enumerate(slugs)
    )
    scope_phrase = "/".join(slugs)
    enum_options = " | ".join(f'"{s}"' for s in slugs)
    return (
        "You classify customer messages for the PartSelect chat agent.\n"
        f"PartSelect supports ONLY {appliance_list} appliance parts.\n\n"
        "Rules:\n"
        f"1. Set appliance_type to {quoted}, or 'unknown' "
        "(unknown = appliance-related but type unclear).\n"
        "2. Extract model_number if the customer mentions one, otherwise null.\n"
        "3. Set is_out_of_scope=true when the question is NOT about:\n"
        f"   - {appliance_or_list} parts, symptoms, installation, or compatibility\n"
        "   - PartSelect order status\n"
        "   Out-of-scope examples: ovens, microwaves, HVAC, "
        "general cooking, unrelated topics, small talk.\n"
        "4. If the user asks multiple questions, classify the dominant in-scope "
        f"{scope_phrase} support intent. Do not force a model number onto "
        "an appliance if the surrounding text suggests they may not match.\n\n"
        "Respond with ONLY a JSON object — no markdown, no explanation:\n"
        '{"appliance_type": ' + enum_options + ' | "unknown", '
        '"model_number": "<string>" | null, "is_out_of_scope": true | false}'
    )


def _build_supervisor_decision_model(slugs: list[str]):
    ApplianceTypeLiteral = Literal[tuple(slugs + ["unknown"])]  # type: ignore[valid-type]
    return create_model(
        "SupervisorDecision",
        appliance_type=(ApplianceTypeLiteral, ...),
        model_number=(Optional[str], None),
        is_out_of_scope=(bool, False),
    )


_SUPERVISOR_SYSTEM = _build_supervisor_system(_ACTIVE_SLUGS)
_SupervisorDecision = _build_supervisor_decision_model(_ACTIVE_SLUGS)
_structured_supervisor = _supervisor_model.with_structured_output(_SupervisorDecision)


def _is_order_followup(user_msg: str, state: AgentState) -> bool:
    """Detect short follow-ups to an order-tracking clarification."""
    if not re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", user_msg):
        return False

    for msg in reversed(state["messages"][:-1]):
        if isinstance(msg, AIMessage):
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            lowered = content.lower()
            return "order" in lowered and "email" in lowered
    return False


def _lookup_model_appliance(model_number: str) -> Optional[str]:
    """Return the appliance category slug for a known model number."""
    cleaned = model_number.strip().strip("?.!,;:").upper()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT ac.slug
            FROM models m
            JOIN appliance_categories ac ON ac.id = m.category_id
            WHERE m.model_number = ?
            """,
            (cleaned,),
        ).fetchone()
        return row["slug"] if row else None
    finally:
        conn.close()


def supervisor_node(state: AgentState) -> dict:
    user_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_msg = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    if _is_order_followup(user_msg, state):
        return {
            "appliance_type": "unknown",
            "model_number": None,
            "is_out_of_scope": False,
        }

    try:
        decision = _structured_supervisor.invoke([
            SystemMessage(content=_SUPERVISOR_SYSTEM),
            HumanMessage(content=user_msg),
        ])
        model_number = decision.model_number
        if model_number:
            model_appliance = _lookup_model_appliance(model_number)
            if (
                model_appliance
                and decision.appliance_type in _ACTIVE_SLUGS
                and model_appliance != decision.appliance_type
            ):
                model_number = None
        return {
            "appliance_type": decision.appliance_type,
            "model_number": model_number,
            "is_out_of_scope": decision.is_out_of_scope,
        }
    except Exception:
        return {"appliance_type": "unknown", "model_number": None, "is_out_of_scope": False}


# ---------------------------------------------------------------------------
# Specialist node
# ---------------------------------------------------------------------------

def specialist_node(state: AgentState) -> dict:
    appliance_type = state.get("appliance_type") or "unknown"
    config = _load_specialist_config(appliance_type)
    system_prompt = config.get("system_prompt_context", _FALLBACK_SYSTEM_PROMPT).strip()
    system_prompt += (
        "\n\nIf the customer asks multiple questions, answer each one clearly "
        "when the context is unambiguous. If a model number appears to conflict "
        "with the appliance type mentioned by the customer, ask them to confirm "
        "the correct model number instead of treating that model as compatible context."
        "\n\nOrder tracking is in scope. If an order lookup returns no result, "
        "tell the customer that no matching order was found for that order number "
        "and email combination, then ask them to double-check both values or "
        "contact PartSelect support. For a new order lookup, do not reuse an "
        "email from earlier conversation history unless the customer confirms "
        "that email in the current turn."
    )

    model_number = state.get("model_number")
    if model_number:
        system_prompt += f"\n\nThe customer's appliance model number is: {model_number}"

    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    response = _specialist_with_tools.invoke(messages)
    return {"messages": [response]}


# ---------------------------------------------------------------------------
# Decline node — out-of-scope questions, bypasses specialist + validator
# ---------------------------------------------------------------------------

def _build_decline_content(slugs: list[str]) -> str:
    bold_list = " and ".join(f"**{s}**" for s in slugs)
    question_list = " or ".join(f"your {s}" for s in slugs)
    return (
        f"I'm here to help with {bold_list} parts only — "
        "finding parts, checking compatibility, troubleshooting symptoms, "
        "installation guides, and order tracking.\n\n"
        "For other appliance types or general questions, please visit "
        "[partselect.com](https://www.partselect.com) or contact PartSelect "
        "support at **1-888-738-4871**.\n\n"
        f"Is there anything I can help you with for {question_list}?"
    )


_DECLINE_CONTENT = _build_decline_content(_ACTIVE_SLUGS)


def decline_node(state: AgentState) -> dict:
    return {
        "messages": [AIMessage(content=_DECLINE_CONTENT)],
        "validator_verdict": "pass",
        "validator_feedback": "Out-of-scope question declined appropriately.",
    }


# ---------------------------------------------------------------------------
# Validator node
# ---------------------------------------------------------------------------

_VALIDATOR_SYSTEM = (
    "You review appliance parts assistant responses for accuracy and safety.\n\n"
    "Verdicts:\n"
    '  "pass"     — accurate, helpful, safe\n'
    '  "warn"     — mostly fine but vague, incomplete, or has a minor issue\n'
    '  "escalate" — safety hazard (gas leak, flooding, electrical fire) OR '
    "clearly wrong part information that could harm the customer\n\n"
    "Respond with ONLY JSON — no markdown, no explanation:\n"
    '{"verdict": "pass" | "warn" | "escalate", "feedback": "<one sentence>"}'
)

_ESCALATION_CONTENT = (
    "This situation may involve a safety hazard. "
    "Please stop using the appliance immediately and contact PartSelect support "
    "at 1-888-738-4871, or call a licensed technician."
)


class _ValidatorOutput(BaseModel):
    verdict: Literal["pass", "warn", "escalate"]
    feedback: str


_structured_validator = _validator_model.with_structured_output(_ValidatorOutput)


def validator_node(state: AgentState) -> dict:
    specialist_response = ""
    user_question = ""

    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and not specialist_response:
            content = msg.content
            specialist_response = content if isinstance(content, str) else str(content)
        elif isinstance(msg, HumanMessage) and not user_question:
            content = msg.content
            user_question = content if isinstance(content, str) else str(content)
        if specialist_response and user_question:
            break

    try:
        result = _structured_validator.invoke([
            SystemMessage(content=_VALIDATOR_SYSTEM),
            HumanMessage(content=(
                f"User question:\n{user_question}\n\n"
                f"Specialist response:\n{specialist_response}"
            )),
        ])
        verdict = result.verdict
        feedback = result.feedback
    except Exception as exc:
        verdict = "pass"
        feedback = f"Validator unavailable ({exc!s}) — auto-passed."

    updates: dict = {
        "validator_verdict": verdict,
        "validator_feedback": feedback,
    }

    if verdict == "escalate":
        updates["messages"] = [AIMessage(content=_ESCALATION_CONTENT)]

    return updates
