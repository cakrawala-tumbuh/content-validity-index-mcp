# content-validity-index-mcp

MCP Server berbasis [FastMCP](https://gofastmcp.com) untuk
[content-validity-index-backend](https://github.com/cakrawala-tumbuh/content-validity-index-backend).
Memungkinkan AI client (Claude Desktop, Claude Code, Claude Web) menelusuri
instrumen, item, dimensi, penugasan expert, dan **menghitung Content Validity
Index (CVI)** lewat antarmuka MCP standar.

Bisa dipakai lewat tiga kanal — **stdio**, **Claude Code**, dan **Claude Web
(claude.ai)** — dengan otentikasi memakai **Authentik** sebagai identity
provider (POLA B: issuer yang sama dengan backend, token user diteruskan ke
backend).

## Arsitektur auth (POLA B)

Backend & web app content-validity-index **sudah** memakai Authentik. MCP ini
konsisten dengan keduanya:

```
Claude.ai      ──OAuth Authentik──▶ MCP (AuthentikProvider, issuer = backend)
Claude Code/VS ──API key / token──▶ MCP (BearerApiKeyVerifier)
MCP ──teruskan Bearer <token-user>──▶ content-validity-index-backend
```

- Token diverifikasi seperti backend: **RS256 via JWKS** (OIDC discovery dari
  issuer), **issuer dicek**, audience tidak diverifikasi.
- Klaim `groups` dipetakan ke role dengan logika yang sama: `cvi-admin` → admin,
  selain itu → expert.
- Otorisasi (admin/expert) **ditegakkan backend** — MCP hanya meneruskan token.

## Cara pakai per kanal

### 1. stdio — Claude Desktop / Claude Code lokal

Client men-spawn proses langsung. Untuk stdio, token user diambil dari
`BACKEND_API_TOKEN` (token Authentik milik Anda).

```json
{
  "mcpServers": {
    "content-validity-index": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/cakrawala-tumbuh/content-validity-index-mcp@v0.1.0",
        "content-validity-index-mcp"
      ],
      "env": {
        "BACKEND_API_BASE_URL": "https://cvi-api.example.com",
        "BACKEND_API_TOKEN": "<token-authentik-anda>"
      }
    }
  }
}
```

Atau via Docker (stdio): `command: "docker"`,
`args: ["run","--rm","-i","-e","MCP_TRANSPORT=stdio","-e","BACKEND_API_BASE_URL=...","-e","BACKEND_API_TOKEN=...","ghcr.io/cakrawala-tumbuh/content-validity-index-mcp:latest"]`.

### 2. Claude Code

```bash
# stdio
claude mcp add content-validity-index -- \
  uvx --from "git+https://github.com/cakrawala-tumbuh/content-validity-index-mcp@v0.1.0" \
  content-validity-index-mcp
# remote (server HTTP yang sudah berjalan)
claude mcp add --transport http content-validity-index https://mcp.example.com/mcp
```

### 3. Claude Web (claude.ai) — remote, WAJIB OAuth Authentik

Jalankan server sebagai service HTTP di URL publik HTTPS, lalu daftarkan sebagai
**Custom Connector** di claude.ai. Memerlukan konfigurasi Authentik.

```bash
docker run -d -p 8000:8000 \
  -e MCP_BASE_URL=https://mcp.example.com \
  -e AUTHENTIK_ISSUER_URL=https://auth.example.com/application/o/cvi/ \
  -e AUTHENTIK_CLIENT_ID=... -e AUTHENTIK_CLIENT_SECRET=... \
  -e AUTHENTIK_ADMIN_GROUP=cvi-admin -e AUTHENTIK_EXPERT_GROUP=cvi-expert \
  -e BACKEND_API_BASE_URL=https://cvi-api.example.com \
  ghcr.io/cakrawala-tumbuh/content-validity-index-mcp:latest
```

> Dirilis via GitHub (GitHub Release + image GHCR). Tidak tersedia di PyPI.
> Install dari sumber:
> `pip install "git+https://github.com/cakrawala-tumbuh/content-validity-index-mcp@v0.1.0"`.

## Otentikasi (Authentik)

Server memilih auth otomatis dari environment:

| Mekanisme | Untuk | Aktif jika |
|---|---|---|
| **OAuth Authentik** | Claude Web / browser | `AUTHENTIK_ISSUER_URL` + `CLIENT_ID` + `CLIENT_SECRET` + `MCP_BASE_URL` diisi |
| **API Key statis** | VS Code / CLI | `MCP_API_KEY` diisi (`Authorization: Bearer <key>`) |
| (tanpa auth) | stdio / jaringan lokal | tidak ada yang diisi |

Buat OAuth2/OIDC Provider + Application di Authentik (Redirect URI
`https://<MCP_BASE_URL>/auth/callback`, scope `openid profile email groups`),
**pakai issuer/slug yang sama** dengan backend, lalu isi `AUTHENTIK_*`. Kontrol
akses dilakukan via Policy Binding di Authentik dan role dari `groups`.

## Konfigurasi (environment)

| Variabel | Default | Keterangan |
|---|---|---|
| `BACKEND_API_BASE_URL` | `http://localhost:8000` | Base URL backend (tanpa `/api/v1`) |
| `BACKEND_API_TOKEN` | — | Token Authentik untuk pemakaian stdio/lokal |
| `MCP_TRANSPORT` | `stdio` | `stdio`, `http`, atau `sse` |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8000` | bind saat http/sse |
| `MCP_BASE_URL` | — | URL publik (wajib untuk OAuth Authentik) |
| `AUTHENTIK_ISSUER_URL` | — | Issuer OIDC (sama dengan backend) |
| `AUTHENTIK_CLIENT_ID` / `_SECRET` | — | Kredensial OAuth2 Provider |
| `AUTHENTIK_ADMIN_GROUP` | `cvi-admin` | Group → role admin |
| `AUTHENTIK_EXPERT_GROUP` | `cvi-expert` | Group → role expert |
| `MCP_API_KEY` | — | API key untuk klien non-OAuth |

Deployment cloud memakai uvicorn:
`uvicorn content_validity_index_mcp.asgi:app --host 0.0.0.0 --port 8000`.

## Tools

| Tool | Deskripsi |
|---|---|
| `whoami` | Sinkronkan & tampilkan profil + role user (POST `/auth/sync`) |
| `list_instruments` | Daftar instrumen yang dapat diakses user |
| `get_instrument` | Detail satu instrumen |
| `list_instrument_items` | Daftar item pada instrumen |
| `list_instrument_domains` | Daftar dimensi/domain pada instrumen (termasuk `background_color`) |
| `create_instrument_domain` | Buat dimensi/domain baru, termasuk warna latar `background_color` (admin) |
| `update_instrument_domain` | Perbarui dimensi/domain, termasuk warna latar `background_color` (admin) |
| `delete_instrument_domain` | Hapus dimensi/domain dari instrumen (admin) |
| `calculate_cvi` | Hitung hasil CVI (I-CVI, S-CVI) sebuah instrumen (admin) |
| `list_my_assignments` | Daftar penugasan penilaian milik expert |
| `list_assignment_ratings` | Daftar rating pada sebuah penugasan |

## Pengembangan

```bash
pip install -e .
python -m content_validity_index_mcp     # jalankan lokal (stdio)
make test                                # gate test (lint + unit) di Docker
```

## Lisensi

[MIT](LICENSE).
