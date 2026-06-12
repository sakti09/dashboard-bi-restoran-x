"""Halaman 6 — Developer · Transaksi (teknis). Analisis lengkap klaster tingkat
transaksi (per nota): penentuan K (Elbow/Silhouette/DBI), perbandingan K-Means vs
K-Means++, korelasi fitur, proyeksi PCA 2D/3D, sebaran, dan komposisi klaster.
Hasil hanya tampil setelah menekan 'Run model'."""
import streamlit as st
import pandas as pd
from sklearn.decomposition import PCA
from core.ui import page_header, _md
from core.data import download_button
from core.session import ensure_data_loaded
from core import cluster, charts
from core import transaksi as trx

# fitur dasar untuk heatmap korelasi (memperlihatkan dasar pemilihan subset fitur)
BASE_FEATS = ["total_qty", "n_item_unik", "total_net", "total_gross",
              "qty_makanan", "qty_minuman"]
KMAX = 10  # rentang K sesuai Notebook 04 (k = 2..10)


def num(x):
    return f"{x:,.0f}".replace(",", ".")


page_header(
    "Developer · Transaksi",
    "Eksperimen teknis klaster tingkat transaksi: penentuan K, perbandingan algoritme, "
    "korelasi fitur, proyeksi PCA 2D/3D, dan komposisi klaster.")

df = ensure_data_loaded("Modul Developer · Transaksi")

if "receipt_number" not in df.columns:
    st.warning("Dataset belum memiliki kolom **receipt_number**, sehingga agregasi per "
               "nota tidak dapat dilakukan. Unggah ekspor POS yang menyertakan nomor nota.")
    st.stop()

nota_base = trx.build_transaksi_features(df)
if len(nota_base) < trx.TRX_K + 1:
    st.warning("Data nota tidak cukup untuk analisis pada dataset ini.")
    st.stop()

# ---- kontrol + tombol run ----
c = st.columns([1, 2])
algo_label = c[0].radio("Model", ["K-Means++", "K-Means"])
c[1].markdown("&nbsp;", unsafe_allow_html=True)
run = st.button("Run model", type="primary")

current_cfg = (algo_label,)
if run:
    st.session_state["dev_cfg_trx"] = current_cfg
cfg = st.session_state.get("dev_cfg_trx")

if cfg is None:
    st.info("Pilih **Model** di atas, lalu tekan **Run model** untuk menjalankan "
            "analisis. Hasil tidak ditampilkan sebelum dijalankan.")
    st.stop()
if cfg != current_cfg:
    st.warning("Konfigurasi berubah sejak terakhir dijalankan. Tekan **Run model** "
               "untuk memperbarui hasil di bawah.")

g_algo_label = cfg[0]
g_algo = "kmeans++" if g_algo_label == "K-Means++" else "kmeans"

# ---- praproses + klaster final (winsorize p99 -> Z-score -> K-Means(++), K=5) ----
nota, res, Xz, scaler = trx.run_transaksi_clustering(nota_base, k=trx.TRX_K, algo=g_algo)

# ---- metrik per K (Elbow + validasi) pada ruang fitur yang sama ----
metrik = cluster.metrics_over_k(Xz, 2, KMAX, algo=g_algo)
k_sil = int(metrik.loc[metrik["silhouette"].idxmax(), "K"])
k_dbi = int(metrik.loc[metrik["dbi"].idxmin(), "K"])
k_pakai = trx.TRX_K

fitur_txt = " + ".join(trx.FEATURE_LABEL.get(x, x) for x in trx.TRX_FEATURES)
_md(f'<div class="src-pill">Model: <strong>{g_algo_label}</strong> &middot; '
    f'Fitur: <strong>{fitur_txt}</strong> &middot; '
    f'Praproses: <strong>winsorize p99 + Z-score</strong> &middot; {num(len(nota))} nota</div>')

st.markdown('<div class="panel-title">Penentuan K — Elbow, Silhouette, DBI</div>',
            unsafe_allow_html=True)
g = st.columns(3)
with g[0]:
    st.plotly_chart(charts.line_metric_over_k(metrik, "SSE_inertia",
                    "Elbow (SSE / Inertia)", "SSE", best_k=k_pakai),
                    use_container_width=True)
with g[1]:
    st.plotly_chart(charts.line_metric_over_k(metrik, "silhouette",
                    "Silhouette (maks lebih baik)", "Silhouette", best_k=k_sil),
                    use_container_width=True)
with g[2]:
    st.plotly_chart(charts.line_metric_over_k(metrik, "dbi",
                    "Davies-Bouldin (min lebih baik)", "DBI", best_k=k_dbi),
                    use_container_width=True)
st.caption(f"Silhouette maksimum pada K={k_sil}; DBI minimum pada K={k_dbi}. "
           f"K yang dipakai: {k_pakai} (mengikuti kesimpulan penelitian — Silhouette "
           f"tertinggi diselaraskan DBI terendah, kandidat dalam rentang ±0,02).")
show = metrik.copy()
show["SSE_inertia"] = show["SSE_inertia"].round(3)
show["silhouette"] = show["silhouette"].round(4)
show["dbi"] = show["dbi"].round(4)
st.dataframe(show, use_container_width=True, hide_index=True)
download_button(show, "Unduh metrik per K (CSV)", "metrik_K_transaksi.csv",
                key="dl_metrik_trx")

# ---- perbandingan K-Means vs K-Means++ (pada K terpilih) ----
st.markdown('<div class="panel-title">Perbandingan K-Means vs K-Means++</div>',
            unsafe_allow_html=True)
rows = []
for nm, a in [("K-Means++", "kmeans++"), ("K-Means (acak)", "kmeans")]:
    r = cluster.run_clustering(Xz, k_pakai, algo=a)
    rows.append({"model": nm, "K": k_pakai, "inertia": round(r["inertia"], 3),
                 "silhouette": round(r["silhouette"], 4), "dbi": round(r["dbi"], 4)})
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
st.caption("Pada n_init=10 kedua inisialisasi mencapai solusi hampir identik. Pada "
           "inisialisasi tunggal, K-Means++ cenderung lebih stabil (ragam antar-percobaan "
           "lebih kecil), sehingga dipilih sebagai algoritme final.")

# ---- heatmap korelasi fitur dasar ----
st.markdown('<div class="panel-title">Korelasi Antar-Fitur Dasar</div>',
            unsafe_allow_html=True)
hcols = [x for x in BASE_FEATS if x in nota.columns]
st.plotly_chart(charts.heatmap_corr(nota.fillna(nota[hcols].median()), hcols,
                "Heatmap Korelasi Fitur Dasar Transaksi"), use_container_width=True)
st.caption("Fitur besaran (total_net, total_gross, total_qty, n_item_unik) saling "
           "berkorelasi tinggi. Dari sini dipilih total_net dan n_item_unik, ditambah "
           "rasio_minuman sebagai sumbu komposisi; ketiganya memiliki VIF di bawah 5 "
           "sehingga multikolinearitas dapat diterima dan PCA tidak diperlukan.")

# ---- proyeksi PCA 2D & 3D (ruang fitur final) ----
st.markdown('<div class="panel-title">Proyeksi PCA 2 Komponen (2D)</div>',
            unsafe_allow_html=True)
pca2 = PCA(n_components=2, random_state=42).fit(Xz)
co2 = pca2.transform(Xz)
v1, v2 = pca2.explained_variance_ratio_[:2] * 100
st.plotly_chart(charts.scatter_pca(co2, nota["cluster"].values,
                "Proyeksi PCA 2D Hasil Klaster", v1, v2), use_container_width=True)

st.markdown('<div class="panel-title">Proyeksi PCA 3 Komponen (3D)</div>',
            unsafe_allow_html=True)
pca3 = PCA(n_components=3, random_state=42).fit(Xz)
co3 = pca3.transform(Xz)
w1, w2, w3 = pca3.explained_variance_ratio_[:3] * 100
st.plotly_chart(charts.scatter_pca_3d(co3, nota["cluster"].values,
                "Proyeksi PCA 3D Hasil Klaster", w1, w2, w3), use_container_width=True)
st.caption(f"Klik & seret untuk memutar grafik 3D. Total varians 3 komponen: {w1+w2+w3:.1f}%.")

# ---- komposisi klaster (bar + pie) ----
st.markdown('<div class="panel-title">Komposisi Klaster</div>', unsafe_allow_html=True)
gc = st.columns(2)
with gc[0]:
    st.plotly_chart(charts.bar_clusters(nota, "cluster", "Jumlah Transaksi per Klaster",
                    agg="count"), use_container_width=True)
with gc[1]:
    st.plotly_chart(charts.pie_clusters(nota, "cluster", "Kontribusi Pendapatan per Klaster",
                    value="total_net", agg="sum"), use_container_width=True)

# ---- sebaran ruang fitur ----
st.markdown('<div class="panel-title">Sebaran Klaster pada Ruang Fitur</div>',
            unsafe_allow_html=True)
pdf = nota[["nota", "cluster"]].copy()
pdf["total_net"] = trx.plot_axis(nota["total_net"], "total_net").values
pdf["n_item_unik"] = trx.plot_axis(nota["n_item_unik"], "n_item_unik").values
st.plotly_chart(charts.scatter_clusters(
    pdf, "total_net", "n_item_unik", "cluster", "Sebaran Nota per Klaster",
    text_col="nota", xlab=trx.FEATURE_LABEL.get("total_net"),
    ylab=trx.FEATURE_LABEL.get("n_item_unik")), use_container_width=True)

# ---- tabel hasil ----
st.markdown('<div class="panel-title">Data Hasil Klaster</div>', unsafe_allow_html=True)
out = nota[["nota", "cluster", "total_net", "total_qty", "n_item_unik",
            "qty_makanan", "qty_minuman", "rasio_minuman", "ada_alkohol", "jam"]].copy()
out["rasio_minuman"] = out["rasio_minuman"].round(2)
out = out.sort_values(["cluster", "total_net"], ascending=[True, False])
st.dataframe(out, use_container_width=True, height=380, hide_index=True)
download_button(out, "Unduh hasil klaster (CSV)", "dev_klaster_transaksi.csv",
                key="dl_dev_trx")
