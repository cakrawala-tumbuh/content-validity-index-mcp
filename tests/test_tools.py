"""Test tool MCP secara in-memory (FastMCP Client) dengan backend di-mock.

Tool memanggil backend lewat singleton client di server.py; semua HTTP di-mock
via respx. Token diambil dari ``BACKEND_API_TOKEN`` (di-seed di conftest).
"""

import httpx
import pytest
from fastmcp import Client

from content_validity_index_mcp.server import mcp


class TestUserTools:
    """Tool profil/sinkronisasi user."""

    @pytest.mark.asyncio
    async def test_whoami(self, respx_mock, base_url):
        respx_mock.post(f"{base_url}/api/v1/auth/sync").mock(
            return_value=httpx.Response(200, json={"id": 1, "email": "a@b.c", "role": "admin"})
        )
        async with Client(mcp) as client:
            result = await client.call_tool("whoami", {})
        assert result.data["role"] == "admin"


class TestInstrumentTools:
    """Tool instrumen & kalkulasi CVI."""

    @pytest.mark.asyncio
    async def test_list_instruments(self, respx_mock, base_url):
        respx_mock.get(f"{base_url}/api/v1/instruments/").mock(
            return_value=httpx.Response(200, json=[{"id": 1, "title": "Skala A"}])
        )
        async with Client(mcp) as client:
            result = await client.call_tool("list_instruments", {})
        assert result.data == [{"id": 1, "title": "Skala A"}]

    @pytest.mark.asyncio
    async def test_get_instrument(self, respx_mock, base_url):
        respx_mock.get(f"{base_url}/api/v1/instruments/inst-5").mock(
            return_value=httpx.Response(200, json={"id": "inst-5", "title": "Skala B"})
        )
        async with Client(mcp) as client:
            result = await client.call_tool("get_instrument", {"instrument_id": "inst-5"})
        assert result.data["id"] == "inst-5"

    @pytest.mark.asyncio
    async def test_get_instrument_404_kembalikan_error(self, respx_mock, base_url):
        respx_mock.get(f"{base_url}/api/v1/instruments/inst-99").mock(
            return_value=httpx.Response(404, text="Not Found")
        )
        async with Client(mcp) as client:
            result = await client.call_tool("get_instrument", {"instrument_id": "inst-99"})
        assert result.data["status_code"] == 404

    @pytest.mark.asyncio
    async def test_list_instrument_domains(self, respx_mock, base_url):
        respx_mock.get(f"{base_url}/api/v1/instruments/inst-4/domains").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"id": "d1", "name": "Kognitif", "background_color": "#FDE68A"},
                    {"id": "d2", "name": "Afektif", "background_color": None},
                ],
            )
        )
        async with Client(mcp) as client:
            result = await client.call_tool("list_instrument_domains", {"instrument_id": "inst-4"})
        # Warna latar dimensi harus diteruskan apa adanya dari backend.
        assert result.data[0]["background_color"] == "#FDE68A"
        assert result.data[1]["background_color"] is None

    @pytest.mark.asyncio
    async def test_create_instrument_domain_mengirim_background_color(self, respx_mock, base_url):
        route = respx_mock.post(f"{base_url}/api/v1/instruments/inst-1/domains").mock(
            return_value=httpx.Response(
                201, json={"id": "d9", "name": "Kognitif", "background_color": "#FDE68A"}
            )
        )
        async with Client(mcp) as client:
            result = await client.call_tool(
                "create_instrument_domain",
                {"instrument_id": "inst-1", "name": "Kognitif", "background_color": "#FDE68A"},
            )
        # Payload yang dikirim ke backend harus memuat warna latar.
        import json as _json

        sent = _json.loads(route.calls.last.request.content)
        assert sent == {"name": "Kognitif", "background_color": "#FDE68A"}
        assert result.data["background_color"] == "#FDE68A"

    @pytest.mark.asyncio
    async def test_update_instrument_domain_hanya_kirim_field_terisi(self, respx_mock, base_url):
        route = respx_mock.patch(f"{base_url}/api/v1/instruments/inst-1/domains/d9").mock(
            return_value=httpx.Response(
                200, json={"id": "d9", "name": "Kognitif", "background_color": "#A7F3D0"}
            )
        )
        async with Client(mcp) as client:
            result = await client.call_tool(
                "update_instrument_domain",
                {"instrument_id": "inst-1", "domain_id": "d9", "background_color": "#A7F3D0"},
            )
        import json as _json

        sent = _json.loads(route.calls.last.request.content)
        # Hanya field yang diisi yang dikirim; name tidak ikut karena tidak diberikan.
        assert sent == {"background_color": "#A7F3D0"}
        assert result.data["background_color"] == "#A7F3D0"

    @pytest.mark.asyncio
    async def test_delete_instrument_domain(self, respx_mock, base_url):
        respx_mock.delete(f"{base_url}/api/v1/instruments/inst-1/domains/d9").mock(
            return_value=httpx.Response(200, json={"message": "Domain berhasil dihapus."})
        )
        async with Client(mcp) as client:
            result = await client.call_tool(
                "delete_instrument_domain",
                {"instrument_id": "inst-1", "domain_id": "d9"},
            )
        assert "message" in result.data

    @pytest.mark.asyncio
    async def test_calculate_cvi(self, respx_mock, base_url):
        respx_mock.get(f"{base_url}/api/v1/instruments/inst-3/cvi").mock(
            return_value=httpx.Response(200, json={"s_cvi_ave": 0.95, "items": []})
        )
        async with Client(mcp) as client:
            result = await client.call_tool("calculate_cvi", {"instrument_id": "inst-3"})
        assert result.data["s_cvi_ave"] == 0.95


class TestAssignmentTools:
    """Tool penugasan & rating."""

    @pytest.mark.asyncio
    async def test_list_my_assignments(self, respx_mock, base_url):
        respx_mock.get(f"{base_url}/api/v1/my-assignments").mock(
            return_value=httpx.Response(200, json=[{"id": 7, "instrument_id": 1}])
        )
        async with Client(mcp) as client:
            result = await client.call_tool("list_my_assignments", {})
        assert result.data == [{"id": 7, "instrument_id": 1}]
