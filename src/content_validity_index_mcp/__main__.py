"""Entrypoint server.

Pilih transport via environment (config.py):
  - ``stdio`` (default) → MCP client lokal (Claude Desktop / Claude Code stdio).
  - ``http`` / ``sse``  → service / remote (Claude Code remote, Claude Web).

Dijalankan via ``python -m content_validity_index_mcp`` atau entrypoint script
``content-validity-index-mcp`` (lihat pyproject). Untuk deployment cloud lewat
uvicorn, gunakan ``content_validity_index_mcp.asgi:app`` (lihat asgi.py).
"""

from __future__ import annotations

from .config import settings
from .server import mcp


def main() -> None:
    """Jalankan MCP server sesuai transport pada konfigurasi."""
    if settings.mcp_transport == "stdio":
        mcp.run()
    else:
        mcp.run(
            transport=settings.mcp_transport,
            host=settings.mcp_host,
            port=settings.mcp_port,
        )


if __name__ == "__main__":
    main()
