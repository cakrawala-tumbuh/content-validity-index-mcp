"""content-validity-index-mcp — MCP server untuk content-validity-index-backend.

Paket ini menyediakan MCP Server (FastMCP) yang memungkinkan AI client
(Claude Desktop, Claude Code, Claude Web) berinteraksi dengan REST API
Content Validity Index melalui antarmuka MCP standar.

Otentikasi memakai **Authentik** sebagai identity provider (POLA B): MCP
memverifikasi token Authentik dengan issuer/JWKS/`groups` yang SAMA seperti
backend, lalu meneruskan token user (pass-through) ke backend.

`__version__` di bawah adalah SUMBER TUNGGAL versi project — dibaca secara
dinamis oleh `pyproject.toml` (`[tool.hatch.version]`).
"""

__version__ = "0.1.1"
