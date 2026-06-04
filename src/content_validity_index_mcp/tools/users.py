"""Tool MCP untuk profil & sinkronisasi user (POLA B).

Memanggil ``POST /api/v1/auth/sync`` backend yang menyinkronkan user Authentik
ke database lokal dan mengembalikan profilnya — sekaligus berfungsi sebagai
``whoami`` (identitas + role dari ``groups``).
"""

from __future__ import annotations

from fastmcp import FastMCP

from ..auth_context import resolve_user_token
from ..client import CviApiClient
from ._helpers import unwrap


def register(mcp: FastMCP, client: CviApiClient) -> None:
    """Daftarkan tool user ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Client backend untuk meneruskan request.
    """

    @mcp.tool
    async def whoami() -> dict:
        """Ambil profil user saat ini dan sinkronkan dari Authentik.

        Memanggil ``POST /api/v1/auth/sync`` di backend: memverifikasi token
        Authentik, menyinkronkan data user (email, nama, role dari ``groups``)
        ke database, lalu mengembalikan profil tersinkron. Berguna untuk
        mengetahui identitas dan role (``admin``/``expert``) sebelum memakai
        tool lain.

        Returns:
            Dict profil user (``id``, ``email``, ``full_name``, ``role``, dst.),
            atau dict ``error`` bila gagal.
        """
        token = resolve_user_token()
        return unwrap(await client.post("/api/v1/auth/sync", token=token))
