"""Unit test untuk auth pintu depan (POLA B) — tanpa Authentik nyata.

Menguji:
  - split_issuer: penurunan base_url & slug dari issuer.
  - role_from_groups: pemetaan groups -> role (sama seperti backend).
  - AuthentikProvider: pembangunan endpoint & ekstraksi klaim (userinfo di-mock).
  - BearerApiKeyVerifier: validasi static API key.
"""

import httpx
import pytest
from fastmcp.server.auth import TokenVerifier
from fastmcp.server.auth.oauth_proxy.proxy import OAuthProxy
from mcp.server.auth.provider import TokenError

from content_validity_index_mcp.auth_provider import (
    AuthentikProvider,
    BearerApiKeyVerifier,
    role_from_groups,
    split_issuer,
)

_ISSUER = "https://auth.example.com/application/o/cvi/"
_USERINFO_URL = "https://auth.example.com/application/o/userinfo/"


class TestSplitIssuer:
    """split_issuer harus menurunkan base_url & slug dengan benar."""

    def test_issuer_valid(self):
        base, slug = split_issuer(_ISSUER)
        assert base == "https://auth.example.com"
        assert slug == "cvi"

    def test_issuer_tanpa_trailing_slash(self):
        base, slug = split_issuer("https://auth.example.com/application/o/cvi")
        assert base == "https://auth.example.com"
        assert slug == "cvi"

    def test_issuer_invalid_raise(self):
        with pytest.raises(ValueError, match="AUTHENTIK_ISSUER_URL"):
            split_issuer("https://auth.example.com/oidc/cvi/")


class TestRoleFromGroups:
    """role_from_groups harus identik dengan logika backend."""

    def test_admin_group(self):
        assert role_from_groups(["cvi-admin"], "cvi-admin", "cvi-expert") == "admin"

    def test_expert_group(self):
        assert role_from_groups(["cvi-expert"], "cvi-admin", "cvi-expert") == "expert"

    def test_default_expert(self):
        assert role_from_groups([], "cvi-admin", "cvi-expert") == "expert"

    def test_admin_menang_atas_expert(self):
        groups = ["cvi-expert", "cvi-admin"]
        assert role_from_groups(groups, "cvi-admin", "cvi-expert") == "admin"


def _make_provider(**kwargs) -> AuthentikProvider:
    """Buat AuthentikProvider dengan konfigurasi default untuk test."""
    defaults = {
        "issuer_url": _ISSUER,
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "base_url": "https://mcp.example.com",
        "admin_group": "cvi-admin",
        "expert_group": "cvi-expert",
    }
    defaults.update(kwargs)
    return AuthentikProvider(**defaults)


class TestAuthentikProvider:
    """AuthentikProvider — endpoint & ekstraksi klaim."""

    def test_subclass_oauthproxy(self):
        assert isinstance(_make_provider(), OAuthProxy)

    def test_userinfo_url_dibangun_dari_issuer(self):
        assert _make_provider()._userinfo_url == _USERINFO_URL

    def test_issuer_url_dinormalisasi(self):
        provider = _make_provider(issuer_url="https://auth.example.com/application/o/cvi")
        assert provider._issuer_url == _ISSUER

    @pytest.mark.asyncio
    async def test_extract_claims_admin(self, respx_mock):
        respx_mock.get(_USERINFO_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "sub": "abc-123",
                    "preferred_username": "andhit-r",
                    "name": "Andhit",
                    "email": "andhit@example.com",
                    "groups": ["cvi-admin"],
                },
            )
        )
        claims = await _make_provider()._extract_upstream_claims({"access_token": "tok"})
        assert claims is not None
        assert claims["username"] == "andhit-r"
        assert claims["role"] == "admin"
        assert claims["email"] == "andhit@example.com"

    @pytest.mark.asyncio
    async def test_extract_claims_default_expert(self, respx_mock):
        respx_mock.get(_USERINFO_URL).mock(
            return_value=httpx.Response(
                200,
                json={"sub": "xyz-1", "preferred_username": "dosen", "groups": []},
            )
        )
        claims = await _make_provider()._extract_upstream_claims({"access_token": "tok"})
        assert claims is not None
        assert claims["role"] == "expert"

    @pytest.mark.asyncio
    async def test_extract_claims_tanpa_access_token_raise(self):
        with pytest.raises(TokenError) as exc_info:
            await _make_provider()._extract_upstream_claims({})
        assert exc_info.value.error == "access_denied"

    @pytest.mark.asyncio
    async def test_extract_claims_userinfo_menolak_raise(self, respx_mock):
        respx_mock.get(_USERINFO_URL).mock(
            return_value=httpx.Response(401, json={"detail": "expired"})
        )
        with pytest.raises(TokenError) as exc_info:
            await _make_provider()._extract_upstream_claims({"access_token": "expired"})
        assert exc_info.value.error == "access_denied"


class TestBearerApiKeyVerifier:
    """BearerApiKeyVerifier — validasi static API key."""

    def test_api_key_kosong_raise(self):
        with pytest.raises(ValueError, match="api_key"):
            BearerApiKeyVerifier(api_key="")

    def test_api_key_spasi_raise(self):
        with pytest.raises(ValueError, match="api_key"):
            BearerApiKeyVerifier(api_key="   ")

    def test_adalah_token_verifier(self):
        assert isinstance(BearerApiKeyVerifier(api_key="x"), TokenVerifier)

    @pytest.mark.asyncio
    async def test_token_cocok(self):
        verifier = BearerApiKeyVerifier(api_key="rahasia")
        result = await verifier.verify_token("rahasia")
        assert result is not None
        assert result.client_id == "api-key-client"

    @pytest.mark.asyncio
    async def test_token_salah(self):
        verifier = BearerApiKeyVerifier(api_key="rahasia")
        assert await verifier.verify_token("salah") is None

    @pytest.mark.asyncio
    async def test_token_kosong(self):
        verifier = BearerApiKeyVerifier(api_key="rahasia")
        assert await verifier.verify_token("") is None
