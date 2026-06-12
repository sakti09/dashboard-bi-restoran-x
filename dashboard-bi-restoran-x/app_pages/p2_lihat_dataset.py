"""Halaman 2 — Lihat Dataset (pemilik). Insight + panel kontrol + unduh sesuai filter."""
import streamlit as st
from core.ui import page_header, under_construction

page_header("Lihat Dataset",
            "Unggah data POS (CSV/XLSX), atur panel kontrol, lihat visualisasi, lalu unduh hasil sesuai filter.")
under_construction(
    "Modul sedang disiapkan",
    "Halaman ini akan memuat: unggah CSV/XLSX, panel kontrol (rentang diskon/net/gross/kuantitas, "
    "fokus 1 kategori, filter multi-kategori), grafik batang & pie, ringkasan, tabel, dan tombol unduh "
    "dataset hasil filter. Dikerjakan pada tahap berikutnya.")
