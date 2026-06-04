"""Utilitas bersama untuk modul tools."""

from __future__ import annotations

from typing import Any

import httpx


def unwrap(response: httpx.Response) -> Any:
    """Kembalikan body JSON bila sukses, atau dict error bila gagal.

    Tidak pernah membocorkan stack trace — hanya status dan pesan dari backend.

    Args:
        response: Response dari backend.

    Returns:
        Body JSON (dict/list) saat status 2xx, atau dict
        ``{"error": ..., "status_code": ...}`` saat gagal.
    """
    if response.is_success:
        return response.json()
    return {"error": response.text, "status_code": response.status_code}
