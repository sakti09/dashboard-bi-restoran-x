"""Halaman 5 — Developer · Menu (teknis). Reproduksi analisis notebook klaster menu:
penentuan K (Elbow/Silhouette/DBI), perbandingan K-Means vs K-Means++, heatmap, PCA."""
import streamlit as st
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from core.ui import page_header, _md
from core.data import download_button
from core.session import ensure_data_loaded
from core import cluster, charts
from core.menu import (build_menu_features, FEATURE_SCHEMES, FEATURE_LABEL, THESIS_K)

FULL_FEATS = ["quantity", "frequency", "net_revenue", "avg_price", "units_per_order"]

page_header("Developer · Menu",
            "Eksperimen teknis klaster tingkat menu: penentuan K, perbandingan algoritme, korelasi fitur, dan proyeksi PCA.")

df = ensure_data_loaded("Modul Developer · Menu")
menu = build_menu_features(df)

# ---- kontrol ----
c = st.columns([1, 1, 2])
grup = c[0].radio("Kelompok", ["makanan", "minuman"], format_func=str.capitalize)
algo_label = c[1].radio("Algoritme", ["K-Means++", "K-Means"])
algo = "kmeans++" if algo_label == "K-Means++" else "kmeans"
scheme_name = c[2].selectbox("Skema fitur", list(FEATURE_SCHEMES.keys()))
feat_cols, is_main = FEATURE_SCHEMES[scheme_name]

sub = menu[menu["grup"] == grup].dropna(subset=feat_cols).reset_index(drop=True)
if len(sub) < 5:
    st.warning("Data tidak cukup untuk analisis pada kelompok ini.")
    st.stop()

# ---- praproses: winsorize p95 -> z-score ----
X = sub[feat_cols].copy()
for col in feat_cols:
    X[col] = cluster.winsorize(X[col], 0.95)
Xz, _ = cluster.standardize(X)

# ---- metrik per K (Elbow + Silhouette + DBI) ----
KMAX = 8
metrik = cluster.metrics_over_k(Xz, 2, KMAX, algo=algo)
k_sil = int(metrik.loc[metrik["silhouette"].idxmax(), "K"])
k_dbi = int(metrik.loc[metrik["dbi"].idxmin(), "K"])
k_pakai = THESIS_K[grup] if is_main else k_sil

fitur_txt = " + ".join(FEATURE_LABEL.get(x, x) for x in feat_cols)
_md(f'<div class="src-pill">Kelompok: <strong>{grup.capitalize()}</strong> &middot; '
    f'Algoritme: <strong>{algo_label}</strong> &middot; Fitur: <strong>{fitur_txt}</strong> '
    f'&middot; {len(sub)} menu</div>')

st.markdown('<div class="panel-title">Penentuan K — Elbow, Silhouette, DBI</div>',
            unsafe_allow_html=True)
g = st.columns(3)
with g[0]:
    st.plotly_chart(charts.line_metric_over_k(metrik, "SSE_inertia",
                    "Elbow (SSE / Inertia)", "SSE", best_k=k_pakai), use_container_width=True)
with g[1]:
    st.plotly_chart(charts.line_metric_over_k(metrik, "silhouette",
                    "Silhouette (maks lebih baik)", "Silhouette", best_k=k_sil),
                    use_container_width=True)
with g[2]:
    st.plotly_chart(charts.line_metric_over_k(metrik, "dbi",
                    "Davies-Bouldin (min lebih baik)", "DBI", best_k=k_dbi),
                    use_container_width=True)

st.caption(f"Silhouette maksimum pada K={k_sil}; DBI minimum pada K={k_dbi}. "
           f"K yang dipakai: {k_pakai}"
           + (" (mengikuti kesimpulan penelitian)." if is_main else " (Silhouette tertinggi)."))
show = metrik.copy()
show["SSE_inertia"] = show["SSE_inertia"].round(3)
show["silhouette"] = show["silhouette"].round(4)
show["dbi"] = show["dbi"].round(4)
st.dataframe(show, use_container_width=True, hide_index=True)
download_button(show, "Unduh metrik per K (CSV)", f"metrik_K_{grup}.csv", key="dl_metrik")

# ---- perbandingan K-Means vs K-Means++ pada K terpilih ----
st.markdown('<div class="panel-title">Perbandingan K-Means vs K-Means++</div>',
            unsafe_allow_html=True)
rows = []
for nm, a in [("K-Means++", "kmeans++"), ("K-Means (acak)", "kmeans")]:
    r = cluster.run_clustering(Xz, k_pakai, algo=a)
    rows.append({"algoritme": nm, "K": k_pakai, "inertia": round(r["inertia"], 3),
                 "silhouette": round(r["silhouette"], 4), "dbi": round(r["dbi"], 4)})
banding = pd.DataFrame(rows)
st.dataframe(banding, use_container_width=True, hide_index=True)

# ---- klaster final (algoritme terpilih) ----
res = cluster.run_clustering(Xz, k_pakai, algo=algo)
sub["cluster"] = res["labels"]

# ---- heatmap korelasi fitur ----
st.markdown('<div class="panel-title">Korelasi Antar-Fitur</div>', unsafe_allow_html=True)
hcols = [x for x in FULL_FEATS if x in sub.columns]
st.plotly_chart(charts.heatmap_corr(sub.fillna(sub[hcols].median()), hcols,
                "Heatmap Korelasi Fitur Menu"), use_container_width=True)
st.caption("Korelasi tinggi (mendekati 1) menandakan fitur saling tumpang tindih — "
           "dasar pemilihan subset fitur pada skema utama.")

# ---- proyeksi PCA (fitur lengkap) ----
st.markdown('<div class="panel-title">Proyeksi PCA (2 Komponen)</div>', unsafe_allow_html=True)
Xfull = sub[hcols].fillna(sub[hcols].median())
Xfull_z, _ = cluster.standardize(Xfull)
pca = PCA(n_components=2)
coords = pca.fit_transform(Xfull_z)
v1, v2 = pca.explained_variance_ratio_[:2] * 100
st.plotly_chart(charts.scatter_pca(coords, sub["cluster"].values,
                "Proyeksi PCA Hasil Klaster", v1, v2), use_container_width=True)

# ---- sebaran hasil klaster pada ruang fitur ----
st.markdown('<div class="panel-title">Sebaran Klaster pada Ruang Fitur</div>',
            unsafe_allow_html=True)
st.plotly_chart(charts.scatter_clusters(sub, feat_cols[0], feat_cols[1], "cluster",
                "Sebaran Menu per Klaster", xlab=FEATURE_LABEL.get(feat_cols[0]),
                ylab=FEATURE_LABEL.get(feat_cols[1])), use_container_width=True)

# ---- tabel hasil ----
st.markdown('<div class="panel-title">Data Hasil Klaster</div>', unsafe_allow_html=True)
out = sub[["items", "category", "cluster"] + hcols].copy()
out["avg_price"] = out["avg_price"].round(0)
out["units_per_order"] = out["units_per_order"].round(2)
out = out.sort_values(["cluster", "quantity"], ascending=[True, False])
st.dataframe(out, use_container_width=True, height=380, hide_index=True)
download_button(out, "Unduh hasil klaster (CSV)", f"dev_klaster_menu_{grup}.csv", key="dl_dev")
