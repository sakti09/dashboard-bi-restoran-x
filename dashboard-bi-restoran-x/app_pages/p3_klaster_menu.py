"""Halaman 3 — Klaster Menu (pemilik). Hasil klaster + kontrol klaster/kategori + unduh CSV."""
import streamlit as st
from core.ui import page_header, under_construction

page_header("Klaster Menu",
            "Segmentasi menu makanan & minuman dengan K-Means++. Pilih kombinasi klaster, lihat & unduh hasilnya.")
under_construction(
    "Modul sedang disiapkan",
    "Halaman ini akan menampilkan data hasil klaster menu (bukan metrik), dengan fitur utama bawaan "
    "hasil kesimpulan penelitian plus beberapa skema fitur alternatif, panel kontrol klaster "
    "(0, 1, gabungan 0+1, 0+1+2, atau semua) dan kategori, serta unduh CSV hasil klaster. Dikerjakan berikutnya.")
