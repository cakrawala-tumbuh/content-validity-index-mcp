"""Unit test untuk CviApiClient — token pass-through ke backend."""

import httpx
import pytest

from content_validity_index_mcp.client import CviApiClient


class TestCviApiClient:
    """CviApiClient harus menyuntikkan Authorization Bearer pada tiap request."""

    @pytest.mark.asyncio
    async def test_get_menyuntik_authorization(self, respx_mock, base_url):
        route = respx_mock.get(f"{base_url}/api/v1/instruments/").mock(
            return_value=httpx.Response(200, json=[{"id": 1}])
        )
        client = CviApiClient()
        try:
            response = await client.get("/api/v1/instruments/", token="user-token")
        finally:
            await client.aclose()

        assert response.status_code == 200
        assert route.calls.last.request.headers["authorization"] == "Bearer user-token"

    @pytest.mark.asyncio
    async def test_post_mengirim_json_dan_token(self, respx_mock, base_url):
        route = respx_mock.post(f"{base_url}/api/v1/auth/sync").mock(
            return_value=httpx.Response(200, json={"id": 1, "role": "expert"})
        )
        client = CviApiClient()
        try:
            response = await client.post("/api/v1/auth/sync", token="abc")
        finally:
            await client.aclose()

        assert response.status_code == 200
        assert route.calls.last.request.headers["authorization"] == "Bearer abc"

    @pytest.mark.asyncio
    async def test_delete_menyuntik_authorization(self, respx_mock, base_url):
        route = respx_mock.delete(f"{base_url}/api/v1/instruments/9").mock(
            return_value=httpx.Response(204)
        )
        client = CviApiClient()
        try:
            response = await client.delete("/api/v1/instruments/9", token="zzz")
        finally:
            await client.aclose()

        assert response.status_code == 204
        assert route.calls.last.request.headers["authorization"] == "Bearer zzz"
