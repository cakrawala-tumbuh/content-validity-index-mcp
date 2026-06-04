"""Test wiring server: pemilihan auth, registrasi tools, dan ASGI app."""

import pytest
from fastmcp import Client

from content_validity_index_mcp.server import mcp


class TestAuthMode:
    """Pemilihan auth di server.py berdasarkan konfigurasi."""

    def test_auth_none_di_lingkungan_test(self):
        """Tanpa AUTHENTIK_* dan MCP_API_KEY, _auth harus None."""
        import content_validity_index_mcp.server as server_mod

        assert server_mod._auth is None


class TestToolsTerdaftar:
    """Semua tool utama harus terdaftar pada server."""

    @pytest.mark.asyncio
    async def test_tools_inti_terdaftar(self):
        async with Client(mcp) as client:
            names = {tool.name for tool in await client.list_tools()}

        for expected in (
            "whoami",
            "list_instruments",
            "get_instrument",
            "calculate_cvi",
            "list_my_assignments",
        ):
            assert expected in names


class TestAsgiApp:
    """asgi.py harus menghasilkan ASGI app yang valid."""

    def test_asgi_app_callable(self):
        import content_validity_index_mcp.asgi as asgi_mod

        assert asgi_mod.app is not None
        assert callable(asgi_mod.app)
