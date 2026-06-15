"""
LangChain @tool wrappers for the 8 backend tool functions.
These are passed to the specialist model via bind_tools() and executed by ToolNode.
"""
import json
from typing import Optional

from langchain_core.tools import tool

from backend.tools import (
    search_parts,
    get_part_detail,
    check_compatibility,
    get_compatible_models,
    list_symptoms,
    diagnose_symptom,
    get_install_guide,
    search_repair_articles,
    get_order_status,
    get_cart_deep_link,
)


@tool
def search_parts_tool(
    query: str,
    appliance_type: Optional[str] = None,
    limit: int = 5,
) -> str:
    """Search the PartSelect parts catalog by keyword (name, description, or OEM part number).
    Set appliance_type to 'refrigerator' or 'dishwasher' to narrow results.
    Returns a JSON list of matching parts with price and stock status."""
    return json.dumps(search_parts(query=query, appliance_type=appliance_type, limit=limit))


@tool
def get_part_detail_tool(part_number: str) -> str:
    """Get full details for a single part by its PartSelect PS number or OEM part number.
    Returns name, brand, price, in_stock flag, description, and appliance type.
    Returns null if the part is not found."""
    return json.dumps(get_part_detail(part_number))


@tool
def check_compatibility_tool(part_number: str, model_number: str) -> str:
    """Check whether a specific part is compatible with a specific appliance model number.
    Returns {compatible: bool, confidence: 'confirmed'|'inferred'|'incompatible_appliance_type'|'unknown'}.
    When compatible is false and confidence is 'incompatible_appliance_type', the part and model
    are for different appliance types — tell the customer clearly that the part is not compatible.
    When compatible is false and confidence is 'unknown', no record exists for this combination.
    Always call this before telling a customer a part fits their model."""
    return json.dumps(check_compatibility(part_number, model_number))


@tool
def get_compatible_models_tool(part_number: str) -> str:
    """Return all appliance model numbers a given part is known to fit.
    Each result includes model_number, brand, display_name, appliance_type, and confidence."""
    return json.dumps(get_compatible_models(part_number))


@tool
def list_symptoms_tool(appliance_type: str) -> str:
    """Return all known symptom IDs and descriptions for an appliance type.
    Call this before diagnose_symptom_tool to discover valid symptom_id values.
    appliance_type: 'refrigerator' or 'dishwasher'
    Returns a JSON list of {id, description, is_safety_critical}."""
    return json.dumps(list_symptoms(appliance_type=appliance_type))


@tool
def diagnose_symptom_tool(
    symptom_id: str,
    model_number: Optional[str] = None,
) -> str:
    """Return ranked parts that fix a known symptom.
    Call list_symptoms_tool first to get valid symptom_id values for the appliance type.
    Provide model_number to filter to parts also compatible with that model."""
    return json.dumps(diagnose_symptom(symptom_id, model_number=model_number))


@tool
def get_install_guide_tool(part_number: str) -> str:
    """Return the ordered installation steps for a part.
    Each step includes instruction, tool_required, and safety_note.
    Returns an empty list if no guide exists for this part."""
    return json.dumps(get_install_guide(part_number))


@tool
def search_repair_articles_tool(
    query: str,
    appliance_type: Optional[str] = None,
    n_results: int = 3,
) -> str:
    """Semantic search over PartSelect repair knowledge articles.
    Best for open-ended troubleshooting questions like 'why is my fridge not cooling?'
    or 'dishwasher leaving standing water'. Returns relevant repair article excerpts.
    Set appliance_type to 'refrigerator' or 'dishwasher' to restrict results."""
    return json.dumps(
        search_repair_articles(query=query, appliance_type=appliance_type, n_results=n_results)
    )


@tool
def get_order_status_tool(order_id: str, customer_email: str) -> str:
    """Look up a customer's parts order by order number and customer email.
    Returns order status, part number, tracking number, and estimated delivery date.
    Ask for the order number and email address if either value is missing.
    Do not call this tool until both the order number and email are available.
    Do not reuse an email from earlier conversation history for a new order lookup
    unless the customer confirms it in the current turn.
    Returns null if the order number and email do not match; explain that no matching
    order was found instead of treating the request as out-of-scope."""
    return json.dumps(get_order_status(order_id, customer_email))


@tool
def get_cart_deep_link_tool(part_number: str, quantity: int = 1) -> str:
    """Create a mock PartSelect cart handoff URL for a part.
    Use this when a customer wants to buy, add, or proceed with a compatible part.
    This does not mutate a real cart; it returns a checkout handoff link."""
    return json.dumps(get_cart_deep_link(part_number, quantity))


ALL_TOOLS = [
    search_parts_tool,
    get_part_detail_tool,
    check_compatibility_tool,
    get_compatible_models_tool,
    list_symptoms_tool,
    diagnose_symptom_tool,
    get_install_guide_tool,
    search_repair_articles_tool,
    get_order_status_tool,
    get_cart_deep_link_tool,
]
