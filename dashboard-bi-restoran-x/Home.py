"""Dashboard BI Restoran X — entry point.
Jalankan dengan:  streamlit run Home.py
"""
import streamlit as st
from core.ui import inject_css, sidebar_brand, sidebar_footer

st.set_page_config(
    page_title="Dashboard BI Restoran X",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
sidebar_brand()

# ---- definisi halaman ----
beranda = st.Page("app_pages/p1_beranda.py", title="Beranda",
                  icon=":material/home:", url_path="beranda", default=True)
lihat = st.Page("app_pages/p2_lihat_dataset.py", title="Lihat Dataset",
                icon=":material/database:", url_path="lihat-dataset")
kmenu = st.Page("app_pages/p3_klaster_menu.py", title="Klaster Menu",
                icon=":material/pie_chart:", url_path="klaster-menu")
ktrx = st.Page("app_pages/p4_klaster_transaksi.py", title="Klaster Transaksi",
               icon=":material/receipt_long:", url_path="klaster-transaksi")
devm = st.Page("app_pages/p5_dev_menu.py", title="Developer · Menu",
               icon=":material/insights:", url_path="developer-menu")
devt = st.Page("app_pages/p6_dev_transaksi.py", title="Developer · Transaksi",
               icon=":material/monitoring:", url_path="developer-transaksi")

nav = st.navigation(
    {
        "Pemilik Restoran": [beranda, lihat, kmenu, ktrx],
        "Pengembang": [devm, devt],
    }
)

sidebar_footer()
nav.run()
