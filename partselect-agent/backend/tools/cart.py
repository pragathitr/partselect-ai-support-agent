from urllib.parse import urlencode


def get_cart_deep_link(part_number: str, quantity: int = 1) -> dict:
    """Return a mock PartSelect cart handoff URL for a part."""
    cleaned_part = part_number.strip().strip("?.!,;:").upper()
    safe_quantity = max(1, min(int(quantity or 1), 10))
    query = urlencode({"partNumber": cleaned_part, "quantity": safe_quantity})
    return {
        "part_number": cleaned_part,
        "quantity": safe_quantity,
        "cart_url": f"https://www.partselect.com/cart/add?{query}",
        "handoff": True,
    }
