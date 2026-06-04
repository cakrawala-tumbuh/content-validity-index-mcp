"""Tool MCP untuk penugasan expert dan penilaian (rating).

Berfokus pada perspektif expert: melihat penugasan miliknya dan penilaian pada
sebuah penugasan. Token user diteruskan ke backend.
"""

from __future__ import annotations

from fastmcp import FastMCP

from ..auth_context import resolve_user_token
from ..client import CviApiClient
from ._helpers import unwrap


def register(mcp: FastMCP, client: CviApiClient) -> None:
    """Daftarkan tool penugasan/rating ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Client backend untuk meneruskan request.
    """

    @mcp.tool
    async def list_my_assignments() -> dict | list:
        """Daftar penugasan penilaian (assignment) milik user expert saat ini.

        Returns:
            List penugasan expert, atau dict ``error`` bila gagal.
        """
        token = resolve_user_token()
        return unwrap(await client.get("/api/v1/my-assignments", token=token))

    @mcp.tool
    async def list_assignment_ratings(assignment_id: str) -> dict | list:
        """Daftar penilaian (rating) pada sebuah penugasan.

        Args:
            assignment_id: ID (UUID) penugasan.

        Returns:
            List rating pada penugasan, atau dict ``error`` bila gagal.
        """
        token = resolve_user_token()
        return unwrap(await client.get(f"/api/v1/assignments/{assignment_id}/ratings", token=token))
