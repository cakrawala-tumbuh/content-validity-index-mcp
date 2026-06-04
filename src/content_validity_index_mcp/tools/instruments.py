"""Tool MCP untuk instrumen, item, dimensi, dan kalkulasi CVI.

Semua tool meneruskan token user ke backend; otorisasi (mis. CVI hanya untuk
admin) ditegakkan backend berdasarkan role user.
"""

from __future__ import annotations

from fastmcp import FastMCP

from ..auth_context import resolve_user_token
from ..client import CviApiClient
from ._helpers import unwrap


def register(mcp: FastMCP, client: CviApiClient) -> None:
    """Daftarkan tool instrumen/CVI ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Client backend untuk meneruskan request.
    """

    @mcp.tool
    async def list_instruments(skip: int = 0, limit: int = 100) -> dict | list:
        """Daftar instrumen penelitian yang dapat diakses user.

        Hasil difilter backend sesuai role: admin melihat semua instrumen,
        expert melihat instrumen yang ditugaskan kepadanya.

        Args:
            skip: Jumlah baris yang dilewati untuk pagination (default 0).
            limit: Jumlah maksimum baris yang dikembalikan (default 100).

        Returns:
            List instrumen, atau dict ``error`` bila gagal.
        """
        token = resolve_user_token()
        return unwrap(
            await client.get(
                "/api/v1/instruments/",
                token=token,
                params={"skip": skip, "limit": limit},
            )
        )

    @mcp.tool
    async def get_instrument(instrument_id: int) -> dict:
        """Ambil detail satu instrumen berdasarkan ID.

        Args:
            instrument_id: ID numerik instrumen.

        Returns:
            Dict detail instrumen, atau dict ``error`` bila tidak ditemukan.
        """
        token = resolve_user_token()
        return unwrap(await client.get(f"/api/v1/instruments/{instrument_id}", token=token))

    @mcp.tool
    async def list_instrument_items(instrument_id: int) -> dict | list:
        """Daftar item (butir) pada sebuah instrumen.

        Args:
            instrument_id: ID numerik instrumen.

        Returns:
            List item instrumen, atau dict ``error`` bila gagal.
        """
        token = resolve_user_token()
        return unwrap(await client.get(f"/api/v1/instruments/{instrument_id}/items", token=token))

    @mcp.tool
    async def list_instrument_domains(instrument_id: int) -> dict | list:
        """Daftar dimensi/domain (beserta definisi konstruk) pada instrumen.

        Setiap domain menyertakan ``background_color`` (hex ``#RRGGBB`` atau
        ``null``), yaitu warna latar dimensi yang dipakai untuk membedakan item
        antar-dimensi pada tabel penilaian expert.

        Args:
            instrument_id: ID numerik instrumen.

        Returns:
            List domain instrumen, atau dict ``error`` bila gagal.
        """
        token = resolve_user_token()
        return unwrap(await client.get(f"/api/v1/instruments/{instrument_id}/domains", token=token))

    @mcp.tool
    async def create_instrument_domain(
        instrument_id: str,
        name: str,
        construct_definition: str | None = None,
        behavioral_indicator_example: str | None = None,
        theory_reference: str | None = None,
        background_color: str | None = None,
    ) -> dict:
        """Buat dimensi/domain baru pada sebuah instrumen (khusus admin).

        Args:
            instrument_id: ID instrumen pemilik domain.
            name: Nama domain/dimensi (wajib).
            construct_definition: Definisi konstruk kisi-kisi (kolom D, opsional).
            behavioral_indicator_example: Contoh indikator perilaku (kolom E, opsional).
            theory_reference: Referensi teori (kolom F, opsional).
            background_color: Warna latar dimensi dalam format hex ``#RRGGBB``
                (mis. ``#FDE68A``, opsional). Dipakai sebagai latar item dimensi
                ini pada tabel penilaian expert.

        Returns:
            Dict domain yang dibuat, atau dict ``error`` bila gagal/tidak
            berwenang.
        """
        token = resolve_user_token()
        payload: dict[str, str] = {"name": name}
        if construct_definition is not None:
            payload["construct_definition"] = construct_definition
        if behavioral_indicator_example is not None:
            payload["behavioral_indicator_example"] = behavioral_indicator_example
        if theory_reference is not None:
            payload["theory_reference"] = theory_reference
        if background_color is not None:
            payload["background_color"] = background_color
        return unwrap(
            await client.post(
                f"/api/v1/instruments/{instrument_id}/domains",
                token=token,
                json=payload,
            )
        )

    @mcp.tool
    async def update_instrument_domain(
        instrument_id: str,
        domain_id: str,
        name: str | None = None,
        construct_definition: str | None = None,
        behavioral_indicator_example: str | None = None,
        theory_reference: str | None = None,
        background_color: str | None = None,
    ) -> dict:
        """Perbarui dimensi/domain pada instrumen (khusus admin).

        Hanya field yang diisi (non-null) yang dikirim ke backend; field yang
        dibiarkan kosong tidak diubah. Untuk mengosongkan sebuah field, gunakan
        antarmuka web (tool ini tidak mengirim nilai null eksplisit).

        Args:
            instrument_id: ID instrumen pemilik domain.
            domain_id: ID domain yang akan diperbarui.
            name: Nama domain baru (opsional).
            construct_definition: Definisi konstruk kisi-kisi (kolom D, opsional).
            behavioral_indicator_example: Contoh indikator perilaku (kolom E, opsional).
            theory_reference: Referensi teori (kolom F, opsional).
            background_color: Warna latar dimensi dalam format hex ``#RRGGBB``
                (mis. ``#A7F3D0``, opsional).

        Returns:
            Dict domain yang diperbarui, atau dict ``error`` bila gagal/tidak
            berwenang.
        """
        token = resolve_user_token()
        payload: dict[str, str] = {}
        if name is not None:
            payload["name"] = name
        if construct_definition is not None:
            payload["construct_definition"] = construct_definition
        if behavioral_indicator_example is not None:
            payload["behavioral_indicator_example"] = behavioral_indicator_example
        if theory_reference is not None:
            payload["theory_reference"] = theory_reference
        if background_color is not None:
            payload["background_color"] = background_color
        return unwrap(
            await client.patch(
                f"/api/v1/instruments/{instrument_id}/domains/{domain_id}",
                token=token,
                json=payload,
            )
        )

    @mcp.tool
    async def delete_instrument_domain(instrument_id: str, domain_id: str) -> dict:
        """Hapus dimensi/domain dari instrumen (khusus admin).

        Item yang terkait domain ini akan kehilangan referensi domain-nya
        (``domain_id`` menjadi null), bukan ikut terhapus.

        Args:
            instrument_id: ID instrumen pemilik domain.
            domain_id: ID domain yang akan dihapus.

        Returns:
            Dict pesan sukses, atau dict ``error`` bila gagal/tidak berwenang.
        """
        token = resolve_user_token()
        return unwrap(
            await client.delete(
                f"/api/v1/instruments/{instrument_id}/domains/{domain_id}",
                token=token,
            )
        )

    @mcp.tool
    async def calculate_cvi(instrument_id: int) -> dict:
        """Hitung hasil Content Validity Index (CVI) sebuah instrumen.

        Mengembalikan I-CVI per item, S-CVI/Ave, S-CVI/UA, dan interpretasinya
        berdasarkan penilaian para expert. Memerlukan akses admin di backend.

        Args:
            instrument_id: ID numerik instrumen yang akan dihitung.

        Returns:
            Dict hasil kalkulasi CVI, atau dict ``error`` bila gagal/tidak
            berwenang.
        """
        token = resolve_user_token()
        return unwrap(await client.get(f"/api/v1/instruments/{instrument_id}/cvi", token=token))
