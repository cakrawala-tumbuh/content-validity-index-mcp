# Changelog

Semua perubahan penting pada project ini didokumentasikan di berkas ini.
Format mengikuti [Keep a Changelog](https://keepachangelog.com/id/1.1.0/) dan
[Semantic Versioning](https://semver.org/lang/id/).

## [Unreleased]

## [0.1.1] - 2026-06-05

### Diperbaiki
- Teruskan token Authentik **upstream** ke backend pada alur OAuth Claude.ai.
  FastMCP `OAuthProxy` memberi klien *reference token* buatannya sendiri (token
  swap) — bukan token Authentik — sehingga MCP yang meneruskan header
  `Authorization` mentah membuat backend menolak dengan 401 "Token tidak valid".
  Token kini diambil dari `get_access_token().token` (token Authentik upstream
  hasil swap, JWT RS256 yang dapat diverifikasi backend). Klien API key statis
  diabaikan agar tidak salah diteruskan.

## [0.1.0] - 2026-06-04

### Ditambahkan
- Kerangka awal MCP Server (FastMCP) untuk content-validity-index-backend.
- Otentikasi Authentik POLA B: verifikasi token dengan issuer/JWKS/`groups` yang
  sama seperti backend; token user diteruskan (pass-through) ke backend.
- Tools baca: `whoami`, `list_instruments`, `get_instrument`,
  `list_instrument_items`, `list_instrument_domains`, `calculate_cvi`,
  `list_my_assignments`, `list_assignment_ratings`.
- Tools kelola dimensi (khusus admin): `create_instrument_domain`,
  `update_instrument_domain`, `delete_instrument_domain` — termasuk pengaturan
  `background_color` (warna latar dimensi, hex `#RRGGBB`) yang dipakai untuk
  membedakan item antar-dimensi pada tabel penilaian expert.
- Dukungan transport `stdio`, `http`, dan `sse` — dipakai via stdio (client lokal),
  Claude Code, dan Claude Web (remote).
- ASGI app (`asgi.py`) untuk deployment Streamable HTTP via uvicorn.
- Dockerfile runtime (non-root, uvicorn), gate test (Makefile + Dockerfile.test),
  workflow rilis (GitHub Release + Docker image ke GHCR), dan workflow test.
