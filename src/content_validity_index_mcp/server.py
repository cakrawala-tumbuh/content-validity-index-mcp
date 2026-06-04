"""Definisi MCP Server (FastMCP) + pemilihan auth otomatis (POLA B).

Auth pintu depan dipilih berdasarkan konfigurasi (lihat config.py):
  - Authentik OAuth (Claude.ai): aktif bila AUTHENTIK_ISSUER_URL + CLIENT_ID +
    CLIENT_SECRET + MCP_BASE_URL diisi. User login via Authentik dengan issuer
    yang SAMA seperti backend; ``groups`` dipetakan ke role.
  - API Key (VS Code/CLI): aktif bila MCP_API_KEY diisi.
  - Keduanya bisa aktif bersamaan via MultiAuth.
  - Tanpa konfigurasi: tanpa auth (hanya untuk stdio / jaringan lokal).

Semua tool meneruskan token user ke backend (pass-through), jadi otorisasi
admin/expert ditegakkan backend — MCP tidak menduplikasi skema auth.
"""

from __future__ import annotations

import logging

from fastmcp import FastMCP

from .client import CviApiClient
from .config import settings

logger = logging.getLogger(__name__)

# ── Pemilihan auth pintu depan ────────────────────────────────────────────────
_auth = None
_authentik_aktif = bool(
    settings.authentik_issuer_url
    and settings.authentik_client_id
    and settings.authentik_client_secret
    and settings.mcp_base_url
)

if _authentik_aktif:
    from fastmcp.server.auth import MultiAuth

    from .auth_provider import AuthentikProvider, BearerApiKeyVerifier

    logger.info("OAuth Authentik AKTIF — issuer: %s", settings.authentik_issuer_url)
    _provider = AuthentikProvider(
        issuer_url=settings.authentik_issuer_url,
        client_id=settings.authentik_client_id,
        client_secret=settings.authentik_client_secret,
        base_url=settings.mcp_base_url,
        admin_group=settings.authentik_admin_group,
        expert_group=settings.authentik_expert_group,
        require_authorization_consent="external",
    )
    if settings.mcp_api_key:
        logger.info("API Key AKTIF (MultiAuth: Authentik OAuth + API Key)")
        _auth = MultiAuth(
            server=_provider,
            verifiers=[BearerApiKeyVerifier(api_key=settings.mcp_api_key)],
        )
    else:
        _auth = _provider

elif settings.mcp_api_key:
    from fastmcp.server.auth import MultiAuth

    from .auth_provider import BearerApiKeyVerifier

    logger.info("API Key AKTIF (tanpa OAuth)")
    _auth = MultiAuth(verifiers=[BearerApiKeyVerifier(api_key=settings.mcp_api_key)])

else:
    logger.warning(
        "Tidak ada auth dikonfigurasi — server terbuka. Isi AUTHENTIK_ISSUER_URL + "
        "CLIENT_ID/SECRET + MCP_BASE_URL untuk deployment Claude Web."
    )

mcp = FastMCP(name=settings.mcp_server_name, auth=_auth)

# ── Client backend (token user diteruskan per-request) ────────────────────────
_client = CviApiClient()

# ── Registrasi tools ──────────────────────────────────────────────────────────
# Import setelah `mcp` & `_client` dibuat untuk menghindari circular import.
from .tools import assignments, instruments, users  # noqa: E402

users.register(mcp, _client)
instruments.register(mcp, _client)
assignments.register(mcp, _client)
