"""ASGI entrypoint untuk deployment HTTP (dipakai uvicorn / Docker).

Auth sudah menempel pada objek ``mcp`` (lihat server.py), jadi modul ini hanya
membungkusnya menjadi ASGI app dengan transport Streamable HTTP — kompatibel
dengan Claude Web (claude.ai) sebagai remote MCP server.

Jalankan:
    uvicorn content_validity_index_mcp.asgi:app --host 0.0.0.0 --port 8000

Catatan: sebagian client lama memakai SSE. Bila perlu, ganti menjadi
``mcp.http_app(transport="sse")`` (endpoint ``/sse``).
"""

import logging

from .server import mcp

logger = logging.getLogger(__name__)

# Streamable HTTP (default). Auth dihandle di dalam mcp — tanpa wrapper tambahan.
app = mcp.http_app()
logger.info("ASGI app siap (Streamable HTTP)")
