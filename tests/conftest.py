"""Fixtures pytest untuk seluruh test suite content-validity-index-mcp.

Semua HTTP ke backend / Authentik di-mock dengan respx — tidak ada koneksi
nyata. Token user di-seed via settings agar tool dapat berjalan tanpa konteks
request HTTP (in-memory FastMCP Client).
"""

import pytest
import respx

from content_validity_index_mcp.config import settings


@pytest.fixture(autouse=True)
def seed_backend_token():
    """Seed token backend dummy sebelum setiap test, reset setelahnya.

    Membuat ``resolve_user_token`` mengembalikan token tanpa perlu request HTTP.

    Yields:
        None.
    """
    original = settings.backend_api_token
    settings.backend_api_token = "test-token"
    yield
    settings.backend_api_token = original


@pytest.fixture
def base_url():
    """Base URL backend dari settings (tanpa trailing slash).

    Returns:
        String base URL backend.
    """
    return settings.backend_api_base_url.rstrip("/")


@pytest.fixture
def respx_mock():
    """Router respx aktif yang meng-intercept semua request httpx.

    Yields:
        Instance ``respx.MockRouter`` yang aktif.
    """
    with respx.mock(assert_all_called=False) as mock:
        yield mock
