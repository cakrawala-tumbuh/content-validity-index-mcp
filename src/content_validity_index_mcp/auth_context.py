"""Resolusi token user untuk pass-through ke backend (POLA B).

Pada POLA B, MCP **meneruskan token Authentik milik user** ke backend
content-validity-index-backend (yang memverifikasi token via JWKS Authentik).

Sumber token bergantung pada alur otentikasi:

* **OAuth Authentik (Claude.ai via ``OAuthProxy``).** Token yang dipegang klien
  adalah *reference token* buatan FastMCP — **bukan** JWT Authentik. FastMCP
  melakukan *token swap*: hasil validasi (``get_access_token``) membawa token
  **upstream Authentik** (JWT RS256) yang dapat diverifikasi backend. Karena itu
  token diambil dari ``get_access_token().token``, bukan dari header
  ``Authorization`` mentah (yang hanya berisi reference token FastMCP dan akan
  ditolak backend dengan 401 "Token tidak valid").
* **Klien yang mengirim token Authentik langsung** (mis. JWTVerifier tunggal):
  ``get_access_token().token`` sama dengan token yang dikirim — tetap benar.
* **stdio/lokal** (mis. Claude Desktop) tanpa request HTTP: fallback
  ``BACKEND_API_TOKEN``.
"""

from __future__ import annotations

import logging

from fastmcp.exceptions import ToolError

from .config import settings

logger = logging.getLogger(__name__)

_BEARER_PREFIX = "bearer "

# client_id yang disetel ``BearerApiKeyVerifier`` untuk klien API key statis.
# Token klien semacam ini adalah ``MCP_API_KEY`` (bukan token Authentik), jadi
# sengaja diabaikan saat resolusi token pass-through ke backend.
_API_KEY_CLIENT_ID = "api-key-client"


def resolve_user_token() -> str:
    """Ambil token Authentik milik user untuk diteruskan ke backend.

    Urutan resolusi:
      1. Token Authentik upstream dari AccessToken hasil validasi FastMCP
         (``get_access_token``) — benar untuk alur OAuth ``OAuthProxy`` (Claude.ai)
         maupun klien yang mengirim token Authentik langsung.
      2. Header ``Authorization: Bearer <token>`` mentah dari request HTTP —
         fallback bila konteks AccessToken tak tersedia.
      3. Fallback ``BACKEND_API_TOKEN`` dari environment (stdio/lokal).

    Returns:
        Token Bearer (tanpa prefix ``Bearer``) untuk diteruskan ke backend.

    Raises:
        ToolError: Bila tidak ada token pada konteks request maupun environment.
    """
    token = _token_from_access_token() or _token_from_request()
    if token:
        return token

    if settings.backend_api_token:
        return settings.backend_api_token

    raise ToolError(
        "Token user tidak tersedia. Akses lewat HTTP dengan header "
        "'Authorization: Bearer <token-authentik>', atau set BACKEND_API_TOKEN "
        "untuk pemakaian stdio/lokal."
    )


def _token_from_access_token() -> str | None:
    """Ambil token Authentik upstream dari AccessToken hasil validasi FastMCP.

    Pada alur ``OAuthProxy`` (Claude.ai), FastMCP menyimpan token **upstream
    Authentik** (hasil *token swap*) pada AccessToken request — bukan reference
    token yang dipegang klien. ``get_access_token().token`` mengembalikan token
    upstream itu, yakni JWT RS256 yang dapat diverifikasi backend.

    Token dari klien API key statis (``BearerApiKeyVerifier``, ``client_id`` =
    ``_API_KEY_CLIENT_ID``) sengaja **diabaikan** karena bernilai ``MCP_API_KEY``,
    bukan token Authentik — sehingga resolusi jatuh ke ``BACKEND_API_TOKEN``.

    Returns:
        Token upstream tanpa prefix ``Bearer``, atau ``None`` bila tidak ada
        konteks AccessToken (mis. stdio) atau token berasal dari API key statis.
    """
    try:
        from fastmcp.server.dependencies import get_access_token

        access_token = get_access_token()
    except (ImportError, RuntimeError):
        # RuntimeError: dipanggil di luar konteks request HTTP (mis. stdio).
        return None

    if access_token is None or access_token.client_id == _API_KEY_CLIENT_ID:
        return None
    return access_token.token or None


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
