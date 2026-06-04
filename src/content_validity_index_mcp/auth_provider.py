"""Auth provider pintu depan MCP: Authentik OAuth + API key statis (POLA B).

  AuthentikProvider     — subclass ``OAuthProxy`` yang memakai Authentik sebagai
      identity provider (OAuth 2.0 Authorization Code + PKCE). Token diverifikasi
      via JWKS Authentik dengan **issuer yang sama** seperti backend
      content-validity-index-backend (RS256, tanpa verifikasi audience). Dipakai
      klien berbasis browser (Claude.ai).

  BearerApiKeyVerifier  — ``TokenVerifier`` sederhana untuk static Bearer token,
      dipakai klien non-OAuth (VS Code/CLI).

Keduanya digabung via ``MultiAuth`` di server.py.

POLA B: endpoint Authentik diturunkan dari ``AUTHENTIK_ISSUER_URL`` (issuer yang
sama dengan backend), dan klaim ``groups`` dipetakan ke role dengan logika yang
sama persis seperti ``app/services/user_service.py`` pada backend
(``admin_group`` -> admin, selain itu -> expert). Role tidak menolak akses —
mengikuti backend yang memberi role ``expert`` sebagai default untuk semua user
yang lolos otentikasi Authentik.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastmcp.server.auth import AccessToken, TokenVerifier
from fastmcp.server.auth.oauth_proxy.proxy import OAuthProxy
from fastmcp.server.auth.providers.jwt import JWTVerifier
from mcp.server.auth.provider import TokenError

logger = logging.getLogger(__name__)

_OIDC_PATH_MARKER = "/application/o/"


def split_issuer(issuer_url: str) -> tuple[str, str]:
    """Pisahkan issuer Authentik menjadi ``(base_url, application_slug)``.

    Issuer Authentik berbentuk ``{base}/application/o/{slug}/``. Fungsi ini
    menurunkan ``base`` dan ``slug`` agar endpoint authorize/token/jwks/userinfo
    dapat dibangun tanpa konfigurasi tambahan.

    Args:
        issuer_url: Issuer OIDC Authentik, contoh
            ``https://auth.example.com/application/o/cvi/``.

    Returns:
        Tuple ``(base_url, application_slug)`` — ``base_url`` tanpa trailing
        slash, ``application_slug`` tanpa slash di tepi.

    Raises:
        ValueError: Jika ``issuer_url`` tidak mengandung ``/application/o/``.

    Example:
        >>> split_issuer("https://auth.example.com/application/o/cvi/")
        ('https://auth.example.com', 'cvi')
    """
    issuer = issuer_url.rstrip("/")
    if _OIDC_PATH_MARKER not in issuer:
        raise ValueError(
            "AUTHENTIK_ISSUER_URL harus berbentuk "
            "'{base}/application/o/{slug}/' (sama seperti backend)"
        )
    base, slug = issuer.split(_OIDC_PATH_MARKER, 1)
    return base.rstrip("/"), slug.strip("/")


def role_from_groups(groups: list[str], admin_group: str, expert_group: str) -> str:
    """Petakan daftar ``groups`` Authentik ke role aplikasi.

    Mengikuti logika backend (``user_service.sync_from_claims``): bila user
    anggota ``admin_group`` -> ``admin``; selain itu -> ``expert`` (default).

    Args:
        groups: Daftar nama group dari klaim ``groups`` token Authentik.
        admin_group: Nama group untuk role admin.
        expert_group: Nama group untuk role expert (dipertahankan untuk
            konsistensi penamaan dengan backend; default tetap ``expert``).

    Returns:
        ``"admin"`` bila user anggota ``admin_group``, selain itu ``"expert"``.

    Example:
        >>> role_from_groups(["cvi-admin"], "cvi-admin", "cvi-expert")
        'admin'
        >>> role_from_groups([], "cvi-admin", "cvi-expert")
        'expert'
    """
    if admin_group in groups:
        return "admin"
    if expert_group in groups:
        return "expert"
    return "expert"


class AuthentikProvider(OAuthProxy):
    """OAuthProxy yang memakai Authentik sebagai identity provider (POLA B).

    Endpoint Authentik dibangun dari ``issuer_url`` (issuer yang sama dengan
    backend). Authentik 2024+: authorize & token memakai endpoint generik tanpa
    slug; JWKS/issuer/end-session memakai slug.

    Verifikasi token mengikuti backend: RS256 via JWKS, issuer dicek, audience
    **tidak** diverifikasi (``verify_aud=False`` di backend). Klaim ``groups``
    dipetakan ke role dan disematkan di FastMCP JWT.

    Args:
        issuer_url: Issuer OIDC Authentik (sama dengan backend), contoh
            ``https://auth.example.com/application/o/cvi/``.
        client_id: Client ID OAuth2 Provider di Authentik.
        client_secret: Client Secret OAuth2 Provider di Authentik.
        base_url: URL publik MCP server (untuk redirect OAuth).
        admin_group: Nama group Authentik untuk role admin.
        expert_group: Nama group Authentik untuk role expert.
        **kwargs: Diteruskan ke ``OAuthProxy.__init__``.

    Example:
        >>> provider = AuthentikProvider(
        ...     issuer_url="https://auth.example.com/application/o/cvi/",
        ...     client_id="abc123",
        ...     client_secret="secret",
        ...     base_url="https://mcp.example.com",
        ...     admin_group="cvi-admin",
        ...     expert_group="cvi-expert",
        ... )
    """

    def __init__(
        self,
        *,
        issuer_url: str,
        client_id: str,
        client_secret: str,
        base_url: str,
        admin_group: str = "cvi-admin",
        expert_group: str = "cvi-expert",
        **kwargs: Any,
    ) -> None:
        base, slug = split_issuer(issuer_url)

        authorize_url = f"{base}/application/o/authorize/"
        token_url = f"{base}/application/o/token/"
        jwks_url = f"{base}/application/o/{slug}/jwks/"
        revoke_url = f"{base}/application/o/{slug}/end-session/"
        self._issuer_url = f"{base}/application/o/{slug}/"
        self._userinfo_url = f"{base}/application/o/userinfo/"

        # Mengikuti backend: RS256 via JWKS, issuer dicek, audience tidak diverifikasi.
        token_verifier = JWTVerifier(jwks_uri=jwks_url, issuer=self._issuer_url)

        super().__init__(
            upstream_authorization_endpoint=authorize_url,
            upstream_token_endpoint=token_url,
            upstream_client_id=client_id,
            upstream_client_secret=client_secret,
            upstream_revocation_endpoint=revoke_url,
            token_verifier=token_verifier,
            base_url=base_url,
            valid_scopes=["openid", "profile", "email"],
            **kwargs,
        )

        self._admin_group = admin_group
        self._expert_group = expert_group
        logger.debug(
            "AuthentikProvider siap — issuer: %s | admin_group: %s | expert_group: %s",
            self._issuer_url,
            admin_group,
            expert_group,
        )

    async def _extract_upstream_claims(self, idp_tokens: dict[str, Any]) -> dict[str, Any] | None:
        """Ambil klaim user dari Authentik userinfo dan petakan role.

        Dipanggil sekali saat pertukaran authorization code. Klaim yang diambil
        sama seperti backend (``sub``, ``email``, ``name``/``preferred_username``,
        ``groups``) lalu ``groups`` dipetakan ke role.

        Args:
            idp_tokens: Response token Authentik, berisi ``access_token`` dsb.

        Returns:
            Dict klaim untuk FastMCP JWT: ``username``, ``email``, ``name``,
            ``sub``, ``groups``, ``role``.

        Raises:
            TokenError: Bila ``access_token`` kosong atau userinfo Authentik tak
                terjangkau/menolak token.
        """
        access_token = idp_tokens.get("access_token", "")
        if not access_token:
            raise TokenError("access_denied", "Upstream access token tidak tersedia")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self._userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
        except httpx.RequestError as exc:
            logger.warning("Gagal menghubungi Authentik userinfo: %s", exc)
            raise TokenError(
                "server_error", "Tidak dapat memverifikasi identitas dari Authentik"
            ) from exc

        if response.status_code != 200:
            logger.warning("Authentik userinfo menolak token (status=%d)", response.status_code)
            raise TokenError("access_denied", "Token Authentik tidak valid atau kedaluwarsa")

        userinfo = response.json()
        username: str = (
            (userinfo.get("preferred_username") or userinfo.get("sub", "")).lower().strip()
        )
        if not username:
            raise TokenError("access_denied", "Tidak dapat mengambil username dari Authentik")

        groups: list[str] = userinfo.get("groups", [])
        role = role_from_groups(groups, self._admin_group, self._expert_group)

        logger.info("User Authentik '%s' terautentikasi (role=%s)", username, role)
        return {
            "username": username,
            "email": userinfo.get("email"),
            "name": userinfo.get("name"),
            "sub": userinfo.get("sub"),
            "groups": groups,
            "role": role,
        }


class BearerApiKeyVerifier(TokenVerifier):
    """TokenVerifier yang memvalidasi static Bearer token (API key).

    Untuk klien tanpa OAuth (VS Code/CLI/otomasi). Token valid = nilai persis
    ``MCP_API_KEY``.

    Args:
        api_key: API key statis (wajib non-kosong).

    Raises:
        ValueError: Bila ``api_key`` kosong/spasi.

    Example:
        >>> verifier = BearerApiKeyVerifier(api_key="rahasia")
    """

    def __init__(self, *, api_key: str) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key tidak boleh kosong")
        self._api_key = api_key

    async def verify_token(self, token: str) -> AccessToken | None:
        """Kembalikan AccessToken bila token cocok dengan API key, selain itu None.

        Args:
            token: Bearer token dari header Authorization.

        Returns:
            ``AccessToken`` bila cocok, ``None`` bila tidak.
        """
        if token == self._api_key:
            return AccessToken(token=token, client_id="api-key-client", scopes=[])
        return None
