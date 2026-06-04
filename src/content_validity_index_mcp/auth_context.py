"""Resolusi token user untuk pass-through ke backend (POLA B).

Pada POLA B, MCP **meneruskan token user apa adanya** ke backend
content-validity-index-backend (yang juga memverifikasi token Authentik). Token
diambil dari konteks request HTTP FastMCP (header ``Authorization``). Untuk
pemakaian stdio/lokal (mis. Claude Desktop) yang tidak punya request HTTP,
tersedia fallback ``BACKEND_API_TOKEN``.
"""

from __future__ import annotations

import logging

from fastmcp.exceptions import ToolError

from .config import settings

logger = logging.getLogger(__name__)

_BEARER_PREFIX = "bearer "


def resolve_user_token() -> str:
    """Ambil token Authentik milik user untuk diteruskan ke backend.

    Urutan resolusi:
      1. Header ``Authorization: Bearer <token>`` dari request HTTP FastMCP.
      2. Fallback ``BACKEND_API_TOKEN`` dari environment (stdio/lokal).

    Returns:
        Token Bearer (tanpa prefix ``Bearer``) untuk diteruskan ke backend.

    Raises:
        ToolError: Bila tidak ada token pada konteks request maupun environment.
    """
    token = _token_from_request()
    if token:
        return token

    if settings.backend_api_token:
        return settings.backend_api_token

    raise ToolError(
        "Token user tidak tersedia. Akses lewat HTTP dengan header "
        "'Authorization: Bearer <token-authentik>', atau set BACKEND_API_TOKEN "
        "untuk pemakaian stdio/lokal."
    )


def _token_from_request() -> str | None:
    """Ekstrak Bearer token dari request HTTP FastMCP bila ada.

    Returns:
        Token tanpa prefix ``Bearer``, atau ``None`` bila tidak ada konteks
        request HTTP (mis. transport stdio) atau header Authorization kosong.
    """
    try:
        from fastmcp.server.dependencies import get_http_request

        request = get_http_request()
    except (ImportError, RuntimeError):
        # RuntimeError: dipanggil di luar konteks request HTTP (mis. stdio).
        return None

    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith(_BEARER_PREFIX):
        return auth_header[len(_BEARER_PREFIX) :].strip() or None
    return None
