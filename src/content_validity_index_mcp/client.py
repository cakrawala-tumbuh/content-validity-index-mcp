"""Async HTTP client ke content-validity-index-backend (token pass-through).

``CviApiClient`` membungkus ``httpx.AsyncClient`` dan menyuntikkan header
``Authorization: Bearer <token-user>`` pada setiap request — token milik user
yang diteruskan apa adanya (POLA B), bukan kredensial service account.

Satu instance dipakai bersama oleh semua tool (dibuat di server.py). Semua path
endpoint memakai prefix ``/api/v1`` sesuai backend.
"""

from __future__ import annotations

import httpx

from .config import settings


class CviApiClient:
    """Async HTTP client untuk content-validity-index-backend.

    Token user diteruskan per-request (pass-through). Client ini tidak menyimpan
    kredensial apa pun — otorisasi sepenuhnya ditegakkan backend berdasarkan
    token Authentik yang diteruskan.

    Attributes:
        _client: ``httpx.AsyncClient`` dengan ``base_url`` dari konfigurasi.
    """

    def __init__(self) -> None:
        """Inisialisasi client dengan base URL dan timeout dari konfigurasi."""
        self._client = httpx.AsyncClient(
            base_url=settings.backend_api_base_url.rstrip("/"),
            timeout=settings.http_timeout,
        )

    @staticmethod
    def _auth_headers(token: str) -> dict[str, str]:
        """Bangun header Authorization dari token user.

        Args:
            token: Token Bearer milik user (tanpa prefix ``Bearer``).

        Returns:
            Dict ``{"Authorization": "Bearer <token>"}``.
        """
        return {"Authorization": f"Bearer {token}"}

    async def get(
        self,
        path: str,
        *,
        token: str,
        params: dict | None = None,
    ) -> httpx.Response:
        """Kirim HTTP GET dengan token user.

        Args:
            path: Path endpoint, contoh ``/api/v1/instruments/``.
            token: Token Bearer milik user.
            params: Query parameters opsional.

        Returns:
            ``httpx.Response`` dari backend.
        """
        return await self._client.get(path, headers=self._auth_headers(token), params=params)

    async def post(
        self,
        path: str,
        *,
        token: str,
        json: dict | list | None = None,
    ) -> httpx.Response:
        """Kirim HTTP POST dengan token user dan body JSON.

        Args:
            path: Path endpoint.
            token: Token Bearer milik user.
            json: Body request sebagai dict/list.

        Returns:
            ``httpx.Response`` dari backend.
        """
        return await self._client.post(path, headers=self._auth_headers(token), json=json)

    async def patch(
        self,
        path: str,
        *,
        token: str,
        json: dict | None = None,
    ) -> httpx.Response:
        """Kirim HTTP PATCH dengan token user dan body JSON (partial update).

        Args:
            path: Path endpoint.
            token: Token Bearer milik user.
            json: Body request berisi field yang diubah saja.

        Returns:
            ``httpx.Response`` dari backend.
        """
        return await self._client.patch(path, headers=self._auth_headers(token), json=json)

    async def delete(self, path: str, *, token: str) -> httpx.Response:
        """Kirim HTTP DELETE dengan token user.

        Args:
            path: Path endpoint yang akan dihapus.
            token: Token Bearer milik user.

        Returns:
            ``httpx.Response`` dari backend.
        """
        return await self._client.delete(path, headers=self._auth_headers(token))

    async def aclose(self) -> None:
        """Tutup koneksi HTTP client (dipanggil saat server shutdown)."""
        await self._client.aclose()
