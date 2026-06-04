"""Konfigurasi runtime MCP server via pydantic-settings (POLA B).

content-validity-index-mcp melayani backend yang **sudah** memakai Authentik
sebagai identity provider. Karena itu MCP memverifikasi token Authentik dengan
issuer/JWKS/claim yang SAMA seperti backend, memetakan `groups` ke role dengan
logika yang sama, lalu meneruskan token user (pass-through) ke backend — bukan
login sebagai service account.

Semua nilai dibaca dari environment / file `.env` dan diinstansiasi sekali
sebagai singleton ``settings`` yang diimpor modul lain.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Konfigurasi runtime MCP server (POLA B).

    Attributes:
        mcp_server_name: Nama server yang ditampilkan ke MCP client.
        mcp_log_level: Level logging (DEBUG, INFO, WARNING, ERROR).
        mcp_transport: Transport saat dijalankan via ``python -m
            content_validity_index_mcp`` (``stdio`` default, atau ``http``/``sse``).
        mcp_host: Host bind saat transport http/sse.
        mcp_port: Port bind saat transport http/sse.
        mcp_base_url: URL publik MCP server. WAJIB diisi agar OAuth Authentik
            (Claude.ai) berfungsi. Contoh: ``https://mcp.example.com``.
        authentik_issuer_url: Issuer OIDC Authentik — **harus sama** dengan
            ``AUTHENTIK_ISSUER_URL`` di backend, contoh
            ``https://auth.example.com/application/o/cvi/``. JWKS diturunkan via
            OIDC discovery dari issuer ini.
        authentik_client_id: Client ID OAuth2/OIDC Provider di Authentik.
        authentik_client_secret: Client Secret OAuth2/OIDC Provider di Authentik.
        authentik_admin_group: Nama group Authentik untuk role ``admin``
            (samakan dengan ``AUTHENTIK_ADMIN_GROUP`` backend).
        authentik_expert_group: Nama group Authentik untuk role ``expert``
            (samakan dengan ``AUTHENTIK_EXPERT_GROUP`` backend).
        backend_api_base_url: Base URL backend content-validity-index-backend
            (tanpa ``/api/v1``). Token user diteruskan apa adanya ke sini.
        backend_api_token: Token Authentik statis untuk pemakaian stdio/lokal —
            fallback ketika tidak ada konteks request HTTP (mis. Claude Desktop
            stdio). Kosongkan untuk deployment HTTP yang memakai pass-through.
        http_timeout: Timeout HTTP request ke backend dalam detik.
        mcp_api_key: API key statis untuk klien non-OAuth (VS Code/CLI). Request
            wajib menyertakan ``Authorization: Bearer <key>``.
    """

    mcp_server_name: str = "content-validity-index-mcp"
    mcp_log_level: str = "INFO"

    # Transport (untuk `python -m content_validity_index_mcp`)
    mcp_transport: str = "stdio"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8000

    # URL publik MCP (untuk redirect OAuth Authentik / Claude.ai)
    mcp_base_url: str | None = None

    # Authentik OIDC — SAMAKAN dengan content-validity-index-backend.
    authentik_issuer_url: str | None = None
    authentik_client_id: str | None = None
    authentik_client_secret: str | None = None
    authentik_admin_group: str = "cvi-admin"
    authentik_expert_group: str = "cvi-expert"

    # Backend yang dilayani (token user diteruskan apa adanya ke sini).
    backend_api_base_url: str = "http://localhost:8000"
    backend_api_token: str | None = None
    http_timeout: float = 30.0

    # API key statis untuk klien non-OAuth (VS Code / CLI).
    mcp_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_ignore_empty=True,
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
