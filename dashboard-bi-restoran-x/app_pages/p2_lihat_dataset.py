"""Halaman 2 — Lihat Dataset (pemilik). Upload-first; insight + panel kontrol + unduh."""
import streamlit as st
from core.ui import page_header, _md
from core.data import (load_default_master, load_uploaded, validate_master,
                       download_button, REQUIRED_CORE)
from core.session import has_master, get_master, set_master, master_source, clear_master
from core import charts

# kolom yang diharapkan dari ekspor POS (tanpa 'tahun' yang kosong)
EXPECTED = ["receipt_number", "items", "quantity", "item_price", "gross_sales",
            "discounts", "refunds", "net_sales", "payment_method", "event_type",
            "datetime", "variant", "category", "bulan"]


def num(x):
    return f"{x:,.0f}".replace(",", ".")


def rp(x):
    return "Rp " + num(x)


def rp_short(x):
    a = abs(x)
    if a >= 1e9:
        return f"Rp {x/1e9:.2f} M".replace(".", ",")
    if a >= 1e6:
        return f"Rp {x/1e6:.1f} jt".replace(".", ",")
    return rp(x)


def _slider(col, label, series, key):
    lo, hi = int(series.min()), int(series.max())
    if lo >= hi:
        col.caption(f"{label}: {num(lo)} (nilai tunggal)")
        return (lo, hi)
    return col.slider(label, lo, hi, (lo, hi), key=key)


page_header("Lihat Dataset",
            "Unggah data POS (CSV/XLSX), atur panel kontrol, lihat visualisasi, lalu unduh hasil sesuai filter.")

# ============================ EMPTY STATE ============================
if not has_master():
    left, right = st.columns([1.5, 1])
    with left:
        st.markdown("#### Unggah dataset")
        up = st.file_uploader("Pilih berkas CSV atau XLSX", type=["csv", "xlsx", "xls"],
                              label_visibility="collapsed")
        if up is not None:
            try:
                df = load_uploaded(up)
                ok, msg, miss = validate_master(df)
                if ok:
                    set_master(df, f"Unggahan — {up.name}")
                    st.rerun()
                else:
                    st.error("Struktur belum sesuai. Kolom inti yang belum ada: "
                             + ", ".join(miss))
            except Exception as e:
                st.error(f"Gagal membaca berkas: {e}")
    with right:
        st.markdown("#### Coba cepat")
        st.write("Belum punya berkas? Muat dataset penelitian yang sudah tersedia "
                 "untuk melihat dashboard berjalan.")
        if st.button("Muat dataset penelitian (master 2023–2024)", type="primary"):
            set_master(load_default_master(), "Dataset penelitian — master 2023–2024")
            st.rerun()

    chips = "".join(
        f'<span class="col-chip{" req" if c in REQUIRED_CORE else ""}">{c}</span>'
        for c in EXPECTED)
    _md('<div class="card" style="margin-top:20px;">'
        '<h3 style="font-family:var(--font-display);font-size:14px;color:var(--cream);margin:0 0 8px;">'
        'Format Data yang Didukung</h3>'
        '<p style="font-size:12.8px;color:var(--text-muted);line-height:1.65;margin:0 0 4px;">'
        'Gunakan berkas <strong style="color:var(--olive-200)">.csv</strong> atau '
        '<strong style="color:var(--olive-200)">.xlsx</strong> hasil <strong style="color:var(--olive-200)">'
        'ekspor langsung dari sistem POS</strong> (bukan data olahan bagian keuangan). '
        'Struktur kolom yang diharapkan:</p>'
        f'<div class="col-chips">{chips}</div>'
        '<p style="font-size:11.8px;color:var(--text-dim);margin:8px 0 0;">'
        'Kolom bertanda hijau wajib ada agar dataset dapat diproses: '
        + ", ".join(REQUIRED_CORE) + '.</p></div>')
    st.stop()

# ============================ LOADED STATE ============================
df = get_master()

bar = st.columns([3, 1])
with bar[0]:
    _md(f'<div class="src-pill">Sumber data: <strong>{master_source()}</strong> '
        f'&middot; {num(len(df))} baris</div>')
with bar[1]:
    if st.button("Ganti / hapus dataset"):
        clear_master()
        st.rerun()

# ---- panel kontrol ----
st.markdown('<div class="panel-title">Panel Kontrol</div>', unsafe_allow_html=True)
with st.container(border=True):
    r1 = st.columns(4)
    q_rng = _slider(r1[0], "Kuantitas", df["quantity"], "q")
    d_rng = _slider(r1[1], "Diskon (Rp)", df["discounts"], "d")
    n_rng = _slider(r1[2], "Net sales (Rp)", df["net_sales"], "n")
    g_rng = _slider(r1[3], "Gross sales (Rp)", df["gross_sales"], "g")
    r2 = st.columns([2, 1])
    all_cats = sorted(df["category"].dropna().unique().tolist())
    sel_cats = r2[0].multiselect("Filter kategori (boleh lebih dari satu)",
                                 all_cats, default=all_cats)
    focus = r2[1].selectbox("Fokus 1 kategori", ["(Tidak ada)"] + all_cats)

# ---- terapkan filter ----
f = df[df["quantity"].between(*q_rng) & df["discounts"].between(*d_rng)
       & df["net_sales"].between(*n_rng) & df["gross_sales"].between(*g_rng)]
if sel_cats:
    f = f[f["category"].isin(sel_cats)]

if len(f) == 0:
    st.warning("Tidak ada data yang cocok dengan filter saat ini. Longgarkan rentang atau kategori.")
    st.stop()

# ---- ringkasan ----
m = st.columns(4)
m[0].metric("Baris", num(len(f)))
m[1].metric("Total Net Sales", rp_short(f["net_sales"].sum()))
m[2].metric("Total Gross Sales", rp_short(f["gross_sales"].sum()))
m[3].metric("Total Kuantitas", num(f["quantity"].sum()))

# ---- grafik ----
cc = st.columns([1.4, 1])
with cc[0]:
    st.plotly_chart(charts.bar_top_items(f), use_container_width=True)
with cc[1]:
    st.plotly_chart(charts.donut_category(f), use_container_width=True)

lq = charts.line_quantity_by_month(f)
if lq is not None:
    st.plotly_chart(lq, use_container_width=True)

# ---- mode fokus 1 kategori ----
if focus != "(Tidak ada)":
    st.markdown(f'<div class="panel-title">Fokus Kategori — {focus}</div>',
                unsafe_allow_html=True)
    st.plotly_chart(charts.bar_items_in_category(f, focus), use_container_width=True)
    items_tbl = (f[f["category"] == focus]
                 .groupby("items", as_index=False)
                 .agg(kuantitas=("quantity", "sum"),
                      net_sales=("net_sales", "sum"),
                      transaksi=("receipt_number", "nunique"))
                 .sort_values("net_sales", ascending=False))
    st.dataframe(items_tbl, use_container_width=True, hide_index=True)

# ---- tabel + unduh ----
st.markdown('<div class="panel-title">Data (hasil filter)</div>', unsafe_allow_html=True)
st.dataframe(f, use_container_width=True, height=360, hide_index=True)
download_button(f, "Unduh data hasil filter (CSV)", "dataset_terfilter.csv", key="dl_f")
