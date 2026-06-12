"""Halaman 5 — Developer: Klaster Menu (teknis). Metrik, PCA, heatmap, pilih K-Means/K-Means++."""
import streamlit as st
from core.ui import page_header, under_construction

page_header("Developer · Klaster Menu",
            "Eksperimen teknis lengkap untuk validasi akademis pengelompokan tingkat menu.")
under_construction(
    "Modul sedang disiapkan",
    "Halaman ini akan memuat keluaran lengkap notebook menu: tabel & grafik metrik (Elbow/Silhouette/DBI), "
    "heatmap korelasi, proyeksi PCA, diagram titik tiap metrik, pilihan algoritme K-Means vs K-Means++, "
    "serta unduh hasil. Dikerjakan pada tahap berikutnya.")
