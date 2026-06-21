"""Halaman 3 — Klaster Menu (pemilik). Hasil klaster (data), bukan metrik.
Skema utama (rekomendasi penelitian) berprofil; skema alternatif tanpa profil.
Hasil tampil setelah menekan 'Run model'."""
import streamlit as st
from core.ui import page_header, _md
from core.data import download_button
from core.session import ensure_data_loaded
from core import cluster, charts
from core.menu import (build_menu_features, FEATURE_SCHEMES, FEATURE_LABEL,
                       THESIS_K, profile_clusters)


def num(x):
    return f"{x:,.0f}".replace(",", ".")


page_header("Klaster Menu",
            "Segmentasi menu makanan & minuman dengan K-Means++. Atur kelompok & skema, "
            "jalankan model, lalu telusuri dan unduh hasilnya.")

df = ensure_data_loaded("Modul Klaster Menu")
menu = build_menu_features(df)

# ---- pilihan kelompok & skema + tombol run ----
st.markdown('<div class="panel-title">Konfigurasi Klaster</div>', unsafe_allow_html=True)
with st.container(border=True):
    top = st.columns([1, 2])
    grup = top[0].radio("Kelompok menu", ["makanan", "minuman"],
                        format_func=str.capitalize, horizontal=True)
    scheme_name = top[1].selectbox("Skema fitur", list(FEATURE_SCHEMES.keys()))
    run = st.button("Run model", type="primary")

current_cfg = (grup, scheme_name)
if run:
    st.session_state["menu_cfg"] = current_cfg
cfg = st.session_state.get("menu_cfg")

if cfg is None:
    st.info("Pilih **Kelompok menu** dan **Skema fitur** di atas, lalu tekan **Run model** "
            "untuk menjalankan segmentasi. Hasil tidak ditampilkan sebelum dijalankan.")
    st.stop()
if cfg != current_cfg:
    st.warning("Konfigurasi berubah sejak terakhir dijalankan. Tekan **Run model** "
               "untuk memperbarui hasil di bawah.")

g_grup, g_scheme = cfg
feat_cols, do_profile = FEATURE_SCHEMES[g_scheme]

sub = menu[menu["grup"] == g_grup].dropna(subset=feat_cols).reset_index(drop=True)
if len(sub) < 3:
    st.warning("Data menu pada kelompok ini tidak cukup untuk diklaster.")
    st.stop()

# ---- pipeline: winsorize p95 -> z-score -> K-Means++ ----
X = sub[feat_cols].copy()
for c in feat_cols:
    X[c] = cluster.winsorize(X[c], 0.95)
Xz, _ = cluster.standardize(X)
k = THESIS_K[g_grup] if do_profile else cluster.best_k_by_silhouette(Xz, 2, 6)
res = cluster.run_clustering(Xz, k, algo="kmeans++")
sub["cluster"] = res["labels"]
profil_map = {}
if do_profile:
    sub["profil"], profil_map = profile_clusters(sub)

# ---- info skema ----
fitur_txt = " + ".join(FEATURE_LABEL.get(c, c) for c in feat_cols)
catatan = ("Skema rekomendasi penelitian, lengkap dengan profil menu."
           if do_profile else
           "Skema alternatif pilihan pengguna — tanpa profil; K dipilih otomatis (Silhouette).")
_md(f'<div class="src-pill">Kelompok: <strong>{g_grup.capitalize()}</strong> &middot; '
    f'Fitur: <strong>{fitur_txt}</strong> &middot; Jumlah klaster: <strong>{k}</strong> &middot; '
    f'{len(sub)} menu</div>')
st.caption(catatan)

# ---- panel kontrol klaster & kategori ----
st.markdown('<div class="panel-title">Panel Kontrol</div>', unsafe_allow_html=True)
with st.container(border=True):
    pc = st.columns([1.4, 1])
    clusters_avail = sorted(sub["cluster"].unique().tolist())
    sel_cl = pc[0].multiselect("Tampilkan klaster", clusters_avail,
                               default=clusters_avail,
                               format_func=lambda i: f"Klaster {i}")
    cats = sorted(sub["category"].dropna().unique().tolist())
    sel_cat = pc[1].multiselect("Filter kategori", cats, default=cats)

view = sub[sub["cluster"].isin(sel_cl) & sub["category"].isin(sel_cat)].copy()
if len(view) == 0:
    st.warning("Tidak ada menu untuk kombinasi klaster/kategori ini.")
    st.stop()

# ---- ringkasan tiap klaster (chips) ----
chips = ""
for c in clusters_avail:
    n = int((sub["cluster"] == c).sum())
    col = charts.cluster_color(c)
    extra = f' &middot; {profil_map.get(c)}' if do_profile else ''
    chips += (f'<div class="cl-chip"><span class="cl-dot" style="background:{col}"></span>'
              f'Klaster {c} &middot; {n} menu{extra}</div>')
_md(f'<div class="cl-row">{chips}</div>')

# ---- sebaran hasil klaster (visual hasil, bukan metrik) ----
label_map = profil_map if do_profile else None
fig = charts.scatter_clusters(
    view, x=feat_cols[0], y=feat_cols[1], cluster_col="cluster",
    title="Sebaran Menu per Klaster", label_map=label_map,
    xlab=FEATURE_LABEL.get(feat_cols[0]), ylab=FEATURE_LABEL.get(feat_cols[1]))
st.plotly_chart(fig, use_container_width=True)

# ---- komposisi klaster: diagram batang + lingkaran ----
gc = st.columns(2)
with gc[0]:
    st.plotly_chart(
        charts.bar_clusters(view, "cluster", "Jumlah Menu per Klaster",
                            agg="count", label_map=label_map),
        use_container_width=True)
with gc[1]:
    st.plotly_chart(
        charts.pie_clusters(view, "cluster", "Kontribusi Pendapatan per Klaster",
                            value="net_revenue", agg="sum", label_map=label_map),
        use_container_width=True)

# ---- tabel hasil klaster ----
st.markdown('<div class="panel-title">Data Hasil Klaster</div>', unsafe_allow_html=True)
cols_show = ["items", "category", "cluster"]
if do_profile:
    cols_show.append("profil")
cols_show += ["quantity", "frequency", "net_revenue", "avg_price", "units_per_order"]
tbl = view[cols_show].copy()
tbl["avg_price"] = tbl["avg_price"].round(0)
tbl["units_per_order"] = tbl["units_per_order"].round(2)
tbl = tbl.sort_values(["cluster", "quantity"], ascending=[True, False])
st.dataframe(tbl, use_container_width=True, height=420, hide_index=True)

download_button(tbl, "Unduh hasil klaster (CSV)",
                f"klaster_menu_{g_grup}.csv", key="dl_klaster")
