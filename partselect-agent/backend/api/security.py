"""Small API-key guard for local/prototype deployments."""
from __future__ import annotations

import os
from hmac import compare_digest

from fastapi import Header, HTTPException, status


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Require X-API-Key when APP_API_KEY is configured.

    Leaving APP_API_KEY unset keeps local development friction-free. Setting it
    protects chat and conversation endpoints with a shared server-side key.
    """
    expected = os.getenv("APP_API_KEY")
    if not expected:
        return
    if not x_api_key or not compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
