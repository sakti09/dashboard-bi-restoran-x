"""Halaman 4 — Klaster Transaksi (pemilik). Menampilkan HASIL klaster (data), bukan
metrik teknis. Mereproduksi Notebook 04: 3 fitur (total_net, rasio_minuman,
n_item_unik), winsorize p99, K-Means++ K=5, beserta profil segmen nota."""
import streamlit as st
from core.ui import page_header, _md
from core.data import download_button
from core.session import ensure_data_loaded
from core import cluster, charts
from core import transaksi as trx


def num(x):
    return f"{x:,.0f}".replace(",", ".")


def rp(x):
    return "Rp " + num(x)


page_header(
    "Klaster Transaksi",
    "Segmentasi nota/transaksi dengan K-Means++ untuk strategi promosi. Atur klaster & filter, telusuri profil tiap segmen, lalu unduh hasilnya.")

df = ensure_data_loaded("Modul Klaster Transaksi")

# ---- prasyarat: butuh nomor nota untuk agregasi per transaksi ----
if "receipt_number" not in df.columns:
    st.warning("Dataset belum memiliki kolom **receipt_number**, sehingga agregasi "
               "per nota tidak dapat dilakukan. Unggah ekspor POS yang menyertakan "
               "nomor nota agar modul tingkat transaksi dapat dijalankan.")
    st.stop()

nota = trx.build_transaksi_features(df)
if len(nota) < trx.TRX_K:
    st.warning("Jumlah nota tidak cukup untuk membentuk klaster pada dataset ini.")
    st.stop()

# ---- pipeline penelitian: winsorize p99 -> Z-score -> K-Means++ (K=5) ----
nota, res, _Xz, _sc = trx.run_transaksi_clustering(nota, k=trx.TRX_K, algo="kmeans++")
seg_series, seg_map, reko_map = trx.profile_clusters(nota)
nota["segmen"] = seg_series
short_map = {c: trx.short_label(n) for c, n in seg_map.items()}

# ---- info skema ----
fitur_txt = " + ".join(trx.FEATURE_LABEL.get(c, c) for c in trx.TRX_FEATURES)
_md(f'<div class="src-pill">Fitur: <strong>{fitur_txt}</strong> &middot; '
    f'Praproses: <strong>winsorize p99 + Z-score</strong> &middot; '
    f'Jumlah klaster: <strong>{trx.TRX_K}</strong> &middot; {num(len(nota))} nota</div>')
st.caption("Skema penelitian tingkat transaksi — fitur dipilih melalui uji VIF (semua "
           "di bawah 5, sehingga PCA tidak diperlukan untuk reduksi), dan K=5 ditetapkan "
           "dari Silhouette tertinggi yang diselaraskan dengan DBI terendah.")

# ---- panel kontrol klaster & filter ----
st.markdown('<div class="panel-title">Panel Kontrol</div>', unsafe_allow_html=True)
with st.container(border=True):
    r1 = st.columns([2, 1])
    clusters_avail = sorted(nota["cluster"].unique().tolist())
    sel_cl = r1[0].multiselect(
        "Tampilkan klaster", clusters_avail, default=clusters_avail,
        format_func=lambda i: f"Klaster {i} · {short_map.get(i, i)}")
    alc = r1[1].selectbox("Filter alkohol",
                          ["Semua nota", "Mengandung alkohol", "Tanpa alkohol"])
    r2 = st.columns(2)
    ax_x = r2[0].selectbox("Sumbu X (sebaran)", trx.TRX_FEATURES, index=0,
                           format_func=lambda f: trx.FEATURE_LABEL.get(f, f))
    ax_y_opts = [f for f in trx.TRX_FEATURES if f != ax_x]
    default_y = "n_item_unik" if "n_item_unik" in ax_y_opts else ax_y_opts[0]
    ax_y = r2[1].selectbox("Sumbu Y (sebaran)", ax_y_opts,
                           index=ax_y_opts.index(default_y),
                           format_func=lambda f: trx.FEATURE_LABEL.get(f, f))

# ---- terapkan filter ----
view = nota[nota["cluster"].isin(sel_cl)].copy()
if alc == "Mengandung alkohol":
    view = view[view["ada_alkohol"] == 1]
elif alc == "Tanpa alkohol":
    view = view[view["ada_alkohol"] == 0]
if len(view) == 0:
    st.warning("Tidak ada nota untuk kombinasi klaster/filter ini.")
    st.stop()

# ---- ringkasan tiap klaster (chips) ----
chips = ""
for c in clusters_avail:
    n = int((nota["cluster"] == c).sum())
    col = charts.cluster_color(c)
    chips += (f'<div class="cl-chip"><span class="cl-dot" style="background:{col}"></span>'
              f'Klaster {c} &middot; {num(n)} nota &middot; {short_map.get(c)}</div>')
_md(f'<div class="cl-row">{chips}</div>')

# ---- sebaran hasil klaster (visual hasil, bukan metrik) ----
pdf = view[["nota", "cluster"]].copy()
pdf[ax_x] = trx.plot_axis(view[ax_x], ax_x).values
pdf[ax_y] = trx.plot_axis(view[ax_y], ax_y).values
fig = charts.scatter_clusters(
    pdf, x=ax_x, y=ax_y, cluster_col="cluster", title="Sebaran Nota per Klaster",
    label_map=short_map, text_col="nota",
    xlab=trx.FEATURE_LABEL.get(ax_x), ylab=trx.FEATURE_LABEL.get(ax_y))
st.plotly_chart(fig, use_container_width=True)
st.caption("Setiap titik mewakili satu nota; warna menandai segmen. Sumbu nilai belanja "
           "dan ragam item dibatasi pada persentil ke-99 agar pencilan ekstrem tidak "
           "menekan tampilan sebaran.")

# ---- komposisi klaster: batang (jumlah) + lingkaran (kontribusi pendapatan) ----
gc = st.columns(2)
with gc[0]:
    st.plotly_chart(
        charts.bar_clusters(view, "cluster", "Jumlah Transaksi per Klaster",
                            agg="count", label_map=short_map),
        use_container_width=True)
with gc[1]:
    st.plotly_chart(
        charts.pie_clusters(view, "cluster", "Kontribusi Pendapatan per Klaster",
                            value="total_net", agg="sum", label_map=short_map),
        use_container_width=True)

# ---- profil segmen (kartu) ----
st.markdown('<div class="panel-title">Profil Segmen & Rekomendasi</div>',
            unsafe_allow_html=True)
prof = trx.cluster_profile_table(nota, seg_map, reko_map)
prof = prof[prof["cluster"].isin(sel_cl)]
for _, r in prof.iterrows():
    c = int(r["cluster"])
    col = charts.cluster_color(c)
    stats = (f'<span>Nota: <strong>{num(r["jumlah_nota"])}</strong> ({r["pct_nota"]}%)</span>'
             f'<span>Rata belanja: <strong>{rp(r["rata_belanja"])}</strong></span>'
             f'<span>Ragam item: <strong>{r["rata_jenis"]:.1f}</strong></span>'
             f'<span>Rasio minuman: <strong>{r["rasio_minuman"]:.2f}</strong></span>'
             f'<span>Beralkohol: <strong>{r["pct_beralkohol"]}%</strong></span>'
             f'<span>Jam ramai: <strong>{int(r["jam_median"])}.00</strong></span>'
             f'<span>Kontribusi: <strong>{r["pct_pendapatan"]}%</strong></span>')
    _md(f'<div class="card prof-card" style="border-left:3px solid {col};margin-bottom:12px;">'
        f'<div class="prof-head"><span class="cl-dot" style="background:{col}"></span>'
        f'<strong>Klaster {c} &middot; {r["segmen"]}</strong></div>'
        f'<div class="prof-stats">{stats}</div>'
        f'<p class="prof-reko">{r["rekomendasi_BI"]}</p></div>')

# ---- tabel hasil klaster ----
st.markdown('<div class="panel-title">Data Hasil Klaster</div>', unsafe_allow_html=True)
cols_show = ["nota", "cluster", "segmen", "total_net", "total_qty", "n_item_unik",
             "qty_makanan", "qty_minuman", "rasio_minuman", "ada_alkohol", "jam"]
tbl = view[cols_show].copy()
tbl["rasio_minuman"] = tbl["rasio_minuman"].round(2)
tbl = tbl.sort_values(["cluster", "total_net"], ascending=[True, False])
st.dataframe(tbl, use_container_width=True, height=420, hide_index=True)

download_button(tbl, "Unduh hasil klaster (CSV)", "klaster_transaksi.csv",
                key="dl_klaster_trx")
