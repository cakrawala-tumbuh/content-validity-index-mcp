"""Unit test untuk resolve_user_token (fallback env & error)."""

import pytest
from fastmcp.exceptions import ToolError

from content_validity_index_mcp import auth_context
from content_validity_index_mcp.config import settings


class TestResolveUserToken:
    """resolve_user_token tanpa konteks request HTTP (stdio/in-memory)."""

    def test_fallback_ke_env(self):
        """Tanpa request HTTP, token diambil dari BACKEND_API_TOKEN."""
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
