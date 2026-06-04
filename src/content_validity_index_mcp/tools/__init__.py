"""Paket tools MCP untuk content-validity-index-mcp.

Setiap modul mengekspos fungsi ``register(mcp, client)`` yang mendaftarkan
tool-tool ke instance FastMCP. Semua tool meneruskan token user ke backend
sehingga otorisasi (admin/expert) ditegakkan backend.
"""
