"""Halaman 1 — Beranda. Umum + syarat data (tanpa menampilkan hasil/statistik)."""
from core.ui import page_header, _md
from core.data import REQUIRED_CORE, POS_EXPECTED

page_header(
    "Selamat datang di Dashboard BI Restoran X",
    "Segmentasi penjualan dengan K-Means++ — pilih salah satu modul di bawah untuk memulai.",
)

IC = {
    "data": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/></svg>',
    "pie": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 11h.01"/><path d="M11 15h.01"/><path d="M16 16h.01"/><path d="m2 16 20 6-6-20A20 20 0 0 0 2 16"/><path d="M5.71 17.11a17.04 17.04 0 0 1 11.4-11.4"/></svg>',
    "receipt": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/><path d="M12 17.5v-11"/></svg>',
    "chart": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M7 12v5h12V8l-5 5-4-4Z"/></svg>',
    "chart2": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>',
}


def card(icon, title, desc, href=None, soon=False):
    btn_cls = "btn btn-ghost btn-block" if soon else "btn btn-primary btn-block"
    btn_lbl = "Segera hadir" if soon else "Buka modul"
    inner = (f'<div class="menu-card-icon">{icon}</div>'
             f'<h3>{title}</h3><p>{desc}</p>'
             f'<span class="{btn_cls}">{btn_lbl}</span>')
    if soon:
        return f'<div class="menu-card soon">{inner}</div>'
    return f'<a class="menu-card" href="{href}" target="_self">{inner}</a>'


cards = "".join([
    card(IC["data"], "Lihat Dataset",
         "Unggah data POS (CSV/XLSX), jelajahi insight lewat panel kontrol, lalu unduh hasil sesuai filter.",
         href="lihat-dataset"),
    card(IC["pie"], "Klaster Menu",
         "Segmentasi menu makanan &amp; minuman dengan K-Means++. Kontrol klaster, lihat &amp; unduh hasilnya.",
         href="klaster-menu"),
    card(IC["receipt"], "Klaster Transaksi",
         "Segmentasi tipe nota untuk strategi promosi. Dikembangkan pada tahap penelitian lanjutan.",
         soon=True),
    card(IC["chart"], "Developer &middot; Menu",
         "Eksperimen teknis lengkap: metrik Elbow/Silhouette/DBI, PCA, heatmap, pilih K-Means vs K-Means++.",
         href="developer-menu"),
    card(IC["chart2"], "Developer &middot; Transaksi",
         "Validasi akademis untuk klaster tingkat transaksi. Dikembangkan pada tahap penelitian lanjutan.",
         soon=True),
])
_md(f'<div class="menu-grid">{cards}</div>')

# ---- kartu format/syarat data (umum) ----
_chips = "".join(
    f'<span class="col-chip{" req" if c in REQUIRED_CORE else ""}">{c}</span>'
    for c in POS_EXPECTED)
_md('<div class="card card-cream" style="margin-top:24px;">'
    '<h3>Syarat &amp; Format Data</h3>'
    '<p>Dashboard ini bekerja setelah Anda <strong>memuat dataset</strong> pada tiap modul '
    '(belum ada hasil yang ditampilkan sebelum dijalankan). Berkas dapat berupa '
    '<strong>.csv</strong> maupun <strong>.xlsx</strong>, dan harus merupakan '
    '<strong>hasil ekspor langsung dari sistem POS</strong> (bukan data olahan bagian keuangan). '
    'Struktur kolom yang diharapkan:</p>'
    f'<div class="col-chips">{_chips}</div>'
    '<p style="font-size:11.8px;color:var(--text-dim);margin:8px 0 0;">'
    'Kolom bertanda hijau wajib ada. Kolom <strong>bulan</strong> tidak perlu disertakan — '
    'sistem otomatis menurunkannya dari kolom <strong>datetime</strong> untuk visual bulanan.</p></div>')
