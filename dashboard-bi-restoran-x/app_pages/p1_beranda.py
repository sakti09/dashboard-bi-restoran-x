"""Halaman 1 — Beranda. Mereplikasi desain homepage (dark + olive)."""
import streamlit as st
from core.ui import page_header
from core.data import load_default_master

# ---- statistik ringkas dari dataset master (akurat, ter-cache) ----
try:
    _df = load_default_master()
    n_rows = f"{len(_df):,}".replace(",", ".")
    n_nota = f"{_df['receipt_number'].nunique():,}".replace(",", ".")
    n_item = f"{_df['items'].nunique():,}".replace(",", ".")
    n_kat = f"{_df['category'].nunique():,}".replace(",", ".")
except Exception:
    n_rows, n_nota, n_item, n_kat = "—", "—", "—", "—"

page_header(
    "Selamat datang di Dashboard BI Restoran X",
    "Segmentasi penjualan dengan K-Means++ — pilih salah satu modul di bawah untuk memulai.",
)

# ---- ikon (lucide line icons) ----
IC = {
    "data": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/></svg>',
    "pie": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 11h.01"/><path d="M11 15h.01"/><path d="M16 16h.01"/><path d="m2 16 20 6-6-20A20 20 0 0 0 2 16"/><path d="M5.71 17.11a17.04 17.04 0 0 1 11.4-11.4"/></svg>',
    "receipt": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/><path d="M12 17.5v-11"/></svg>',
    "chart": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M7 12v5h12V8l-5 5-4-4Z"/></svg>',
    "chart2": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>',
}


def card(icon, title, desc, href=None, soon=False):
    btn = ('<span class="btn btn-ghost btn-block">Segera hadir</span>' if soon
           else f'<a class="btn btn-primary btn-block" href="{href}" target="_self">Buka modul</a>')
    return f"""
    <a class="menu-card{' soon' if soon else ''}" {'' if soon else f'href="{href}" target="_self"'}>
      <div class="menu-card-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{desc}</p>
      {btn}
    </a>"""


grid = f"""
<div class="menu-grid">
  {card(IC['data'], "Lihat Dataset", "Unggah data POS (CSV/XLSX), jelajahi insight lewat panel kontrol, lalu unduh hasil sesuai filter.", href="lihat-dataset")}
  {card(IC['pie'], "Klaster Menu", "Segmentasi menu makanan &amp; minuman dengan K-Means++. Kontrol klaster, lihat &amp; unduh hasilnya.", href="klaster-menu")}
  {card(IC['receipt'], "Klaster Transaksi", "Segmentasi tipe nota untuk strategi promosi. Dikembangkan pada tahap penelitian lanjutan.", soon=True)}
  {card(IC['chart'], "Developer &middot; Menu", "Eksperimen teknis lengkap: metrik Elbow/Silhouette/DBI, PCA, heatmap, pilih K-Means vs K-Means++.", href="developer-menu")}
  {card(IC['chart2'], "Developer &middot; Transaksi", "Validasi akademis untuk klaster tingkat transaksi. Dikembangkan pada tahap penelitian lanjutan.", soon=True)}
</div>
"""
st.markdown(grid, unsafe_allow_html=True)

# ---- strip statistik ----
st.markdown(
    f"""
    <div class="stat-row">
      <div class="stat"><div class="v">{n_rows}</div><div class="l">BARIS ITEM-LEVEL</div></div>
      <div class="stat"><div class="v">{n_nota}</div><div class="l">NOTA UNIK</div></div>
      <div class="stat"><div class="v">{n_item}</div><div class="l">ITEM MENU</div></div>
      <div class="stat"><div class="v">{n_kat}</div><div class="l">KATEGORI</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---- kartu tentang ----
st.markdown(
    """
    <div class="card card-cream">
      <h3>Tentang Dashboard Ini</h3>
      <p>
        Dashboard ini dibangun untuk skripsi <strong>SAKTI — Informatika, Universitas Udayana</strong>,
        dengan baseline penelitian data penjualan Restoran X periode Januari 2023 hingga Januari 2024.
        Metode segmentasi yang digunakan adalah <strong>K-Means++</strong> dengan validasi multi-metrik
        (Elbow, Silhouette, Davies-Bouldin). Algoritme referensi: Arthur &amp; Vassilvitskii (2007),
        Rousseeuw (1987), Davies &amp; Bouldin (1979).
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)
