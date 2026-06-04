"""Unit test untuk resolve_user_token (token swap, fallback env, error)."""

import pytest
from fastmcp.exceptions import ToolError
from mcp.server.auth.provider import AccessToken

from content_validity_index_mcp import auth_context
from content_validity_index_mcp.config import settings


class TestResolveUserToken:
    """resolve_user_token: prioritas token upstream, fallback env, error."""

    def test_pakai_token_upstream_dari_access_token(self, monkeypatch):
        """Token Authentik upstream dari get_access_token diprioritaskan.

        Pada alur OAuthProxy (Claude.ai), get_access_token().token berisi token
        Authentik hasil token swap — itulah yang diteruskan ke backend, bukan
        BACKEND_API_TOKEN env (yang sudah di-seed autouse).
        """
        token = AccessToken(token="upstream-authentik-jwt", client_id="claude", scopes=[])
        monkeypatch.setattr("fastmcp.server.dependencies.get_access_token", lambda: token)
        assert auth_context.resolve_user_token() == "upstream-authentik-jwt"

    def test_abaikan_token_api_key_statis(self, monkeypatch):
        """Token klien API key statis diabaikan; jatuh ke BACKEND_API_TOKEN.

        Token klien API key statis bernilai MCP_API_KEY (bukan token Authentik),
        jadi tidak boleh diteruskan ke backend.
        """
        api_token = AccessToken(
            token="static-api-key",
            client_id=auth_context._API_KEY_CLIENT_ID,
            scopes=[],
        )
        monkeypatch.setattr("fastmcp.server.dependencies.get_access_token", lambda: api_token)
        # seed_backend_token (autouse) mengisi "test-token".
        assert auth_context.resolve_user_token() == "test-token"

    def test_fallback_ke_env(self):
        """Tanpa konteks request HTTP, token diambil dari BACKEND_API_TOKEN."""
        # seed_backend_token (autouse) sudah mengisi "test-token".
        assert auth_context.resolve_user_token() == "test-token"

    def test_tanpa_token_raise_toolerror(self):
        """Bila tidak ada token di mana pun, raise ToolError."""
        original = settings.backend_api_token
        settings.backend_api_token = None
        try:
            with pytest.raises(ToolError, match="Token user tidak tersedia"):
                auth_context.resolve_user_token()
        finally:
            settings.backend_api_token = original
