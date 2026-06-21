"""Halaman 4 — Klaster Transaksi (pemilik). Menampilkan HASIL klaster (data), bukan
metrik teknis. Skema rekomendasi penelitian (3 fitur: total_net, rasio_minuman,
n_item_unik; winsorize p99; K-Means++ K=5) berprofil & berlabel segmen. Pengguna dapat
mencoba kombinasi fitur lain — hasilnya hanya bernomor klaster, tanpa pelabelan segmen.
Hasil tampil setelah menekan 'Run model'."""
import json as _json
import streamlit as st
from core.ui import page_header, _md
from core.data import download_button
from core.session import ensure_data_loaded
from core import cluster, charts
from core import transaksi as trx

# Sumbu sebaran dikunci agar insight konsisten: X = nilai belanja, Y = ragam jenis item.
AXIS_X, AXIS_Y = "total_net", "n_item_unik"


def num(x):
    return f"{x:,.0f}".replace(",", ".")


def rp(x):
    return "Rp " + num(x)


def _clicked_cluster(state, cl_order, label_to_cluster):
    """Tafsirkan pilihan klik pada grafik batang/lingkaran menjadi id klaster.
    Mengutamakan label teks (selaras nama segmen/Klaster), lalu indeks titik."""
    if not state:
        return None
    pts = (state.get("selection", {}) or {}).get("points", []) if isinstance(state, dict) else []
    if not pts:
        return None
    p = pts[0]
    for key in ("label", "x"):
        v = p.get(key)
        if v in label_to_cluster:
            return label_to_cluster[v]
    idx = p.get("point_index")
    if idx is None:
        idx = p.get("point_number")
    if idx is not None and 0 <= idx < len(cl_order):
        return int(cl_order[idx])
    return None


page_header(
    "Klaster Transaksi",
    "Segmentasi nota/transaksi dengan K-Means++ untuk strategi promosi. Pilih fitur, "
    "jalankan model, telusuri profil tiap segmen, dan unduh hasilnya.")

df = ensure_data_loaded("Modul Klaster Transaksi")

# ---- prasyarat: butuh nomor nota untuk agregasi per transaksi ----
if "receipt_number" not in df.columns:
    st.warning("Dataset belum memiliki kolom **receipt_number**, sehingga agregasi "
               "per nota tidak dapat dilakukan. Unggah ekspor POS yang menyertakan "
               "nomor nota agar modul tingkat transaksi dapat dijalankan.")
    st.stop()

nota_base = trx.build_transaksi_features(df)
if len(nota_base) < trx.TRX_K:
    st.warning("Jumlah nota tidak cukup untuk membentuk klaster pada dataset ini.")
    st.stop()

# ---- pemilihan fitur + tombol run ----
st.markdown('<div class="panel-title">Konfigurasi Klaster</div>', unsafe_allow_html=True)
with st.container(border=True):
    feats = st.multiselect(
        "Fitur klaster (bawaan = rekomendasi penelitian)",
        trx.CANDIDATE_FEATURES, default=list(trx.TRX_FEATURES),
        format_func=lambda f: trx.FEATURE_LABEL.get(f, f))
    st.caption("Rekomendasi fitur terbaik (hasil uji VIF, semua di bawah 5): Nilai belanja "
               "(net) + Rasio minuman + Ragam jenis item. Bila Anda memilih kombinasi lain, "
               "klaster tetap terbentuk namun hanya ditampilkan sebagai nomor (tanpa "
               "pelabelan segmen), karena bukan konfigurasi terbaik yang ditetapkan pengembang.")
    run = st.button("Run model", type="primary")

current_cfg = tuple(sorted(feats))
if run:
    st.session_state["trx_cfg"] = current_cfg
cfg = st.session_state.get("trx_cfg")

if cfg is None:
    st.info("Pilih **Fitur klaster** di atas (atau biarkan bawaan), lalu tekan **Run model** "
            "untuk menjalankan segmentasi. Hasil tidak ditampilkan sebelum dijalankan.")
    st.stop()
if cfg != current_cfg:
    st.warning("Konfigurasi fitur berubah sejak terakhir dijalankan. Tekan **Run model** "
               "untuk memperbarui hasil di bawah.")

g_feats = list(cfg)
if len(g_feats) < 1:
    st.warning("Pilih minimal satu fitur untuk menjalankan klaster.")
    st.stop()
is_reco = set(g_feats) == set(trx.TRX_FEATURES)

# ---- pipeline: winsorize p99 -> Z-score -> K-Means++ ----
# K=5 (penelitian) untuk kombinasi rekomendasi; Silhouette terbaik untuk kombinasi lain.
if is_reco:
    nota, res, _Xz, _sc = trx.run_transaksi_clustering(nota_base, k=trx.TRX_K, algo="kmeans++")
    k_used = trx.TRX_K
else:
    Xz, _sc = trx.prep_features(nota_base, g_feats)
    k_used = cluster.best_k_by_silhouette(Xz, 2, 6)
    r = cluster.run_clustering(Xz, k_used, algo="kmeans++")
    nota = nota_base.copy()
    nota["cluster"] = r["labels"]

# ---- profiling hanya untuk kombinasi rekomendasi ----
if is_reco:
    seg_series, seg_map, reko_map = trx.profile_clusters(nota)
    nota["segmen"] = seg_series
    short_map = {c: trx.short_label(n) for c, n in seg_map.items()}
    label_map = short_map
else:
    seg_map, reko_map, short_map = {}, {}, {}
    label_map = None  # tampilkan nomor klaster saja

# ---- info skema ----
fitur_txt = " + ".join(trx.FEATURE_LABEL.get(c, c) for c in g_feats)
_md(f'<div class="src-pill">Fitur: <strong>{fitur_txt}</strong> &middot; '
    f'Praproses: <strong>winsorize p99 + Z-score</strong> &middot; '
    f'Jumlah klaster: <strong>{k_used}</strong> &middot; {num(len(nota))} nota</div>')
if is_reco:
    st.caption("Skema penelitian tingkat transaksi — fitur dipilih melalui uji VIF (semua "
               "di bawah 5, sehingga PCA tidak diperlukan untuk reduksi), dan K=5 ditetapkan "
               "dari Silhouette tertinggi yang diselaraskan dengan DBI terendah. Setiap "
               "klaster diberi label segmen beserta rekomendasi bisnis.")
else:
    st.caption("Kombinasi fitur eksplorasi (bukan skema rekomendasi). Jumlah klaster dipilih "
               "otomatis dari Silhouette tertinggi. Hasil ditampilkan sebagai nomor klaster "
               "tanpa pelabelan segmen.")

# ---- panel kontrol tampilan (filter pasca-klaster) ----
st.markdown('<div class="panel-title">Panel Kontrol</div>', unsafe_allow_html=True)
with st.container(border=True):
    r1 = st.columns([2, 1])
    clusters_avail = sorted(nota["cluster"].unique().tolist())
    sel_cl = r1[0].multiselect(
        "Tampilkan klaster", clusters_avail, default=clusters_avail,
        format_func=lambda i: (f"Klaster {i} · {short_map.get(i, i)}" if is_reco
                               else f"Klaster {i}"))
    alc = r1[1].selectbox("Filter alkohol",
                          ["Semua nota", "Mengandung alkohol", "Tanpa alkohol"])

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
    extra = f' &middot; {short_map.get(c)}' if is_reco else ''
    chips += (f'<div class="cl-chip"><span class="cl-dot" style="background:{col}"></span>'
              f'Klaster {c} &middot; {num(n)} nota{extra}</div>')
_md(f'<div class="cl-row">{chips}</div>')

# ---- sebaran hasil klaster (sumbu dikunci: nilai belanja vs ragam jenis item) ----
pdf = view[["nota", "cluster"]].copy()
pdf[AXIS_X] = trx.plot_axis(view[AXIS_X], AXIS_X).values
pdf[AXIS_Y] = trx.plot_axis(view[AXIS_Y], AXIS_Y).values
fig = charts.scatter_clusters(
    pdf, x=AXIS_X, y=AXIS_Y, cluster_col="cluster", title="Sebaran Nota per Klaster",
    label_map=label_map, text_col="nota",
    xlab=trx.FEATURE_LABEL.get(AXIS_X), ylab=trx.FEATURE_LABEL.get(AXIS_Y))
st.plotly_chart(fig, use_container_width=True)
st.caption("Setiap titik mewakili satu nota; warna menandai klaster. Sumbu nilai belanja "
           "dan ragam item dibatasi pada persentil ke-99 agar pencilan ekstrem tidak "
           "menekan tampilan sebaran.")

# ---- komposisi klaster: batang (jumlah) + lingkaran (kontribusi) — DAPAT DIKLIK ----
st.markdown('<div class="panel-title">Komposisi Klaster</div>', unsafe_allow_html=True)
st.caption("Klik salah satu klaster pada diagram batang atau lingkaran untuk menampilkan "
           "rincian kategori menu di dalam klaster tersebut.")
cl_order = sorted(view["cluster"].unique().tolist())
label_to_cluster = {}
for c in cl_order:
    label_to_cluster[(short_map.get(c, f"Klaster {c}") if is_reco else f"Klaster {c}")] = c

gc = st.columns(2)
with gc[0]:
    bar_state = st.plotly_chart(
        charts.bar_clusters(view, "cluster", "Jumlah Transaksi per Klaster",
                            agg="count", label_map=label_map),
        use_container_width=True, key="trx_bar", on_select="rerun")
with gc[1]:
    pie_state = st.plotly_chart(
        charts.pie_clusters(view, "cluster", "Kontribusi Pendapatan per Klaster",
                            value="total_net", agg="sum", label_map=label_map),
        use_container_width=True, key="trx_pie", on_select="rerun")

# deteksi grafik mana yang baru saja diklik (signature berubah pada rerun ini)
sig_bar = _json.dumps(bar_state, sort_keys=True, default=str) if bar_state else ""
sig_pie = _json.dumps(pie_state, sort_keys=True, default=str) if pie_state else ""
prev = st.session_state.get("_trx_drill_sig", {"bar": "", "pie": ""})
drill = st.session_state.get("trx_drill")
# Hanya perbarui bila ada klik baru yang benar-benar mengenai sebuah klaster;
# seleksi kosong (mis. render awal/penghapusan seleksi) tidak menghapus drill aktif.
if sig_bar != prev.get("bar", ""):
    hit = _clicked_cluster(bar_state, cl_order, label_to_cluster)
    if hit is not None:
        drill = hit
elif sig_pie != prev.get("pie", ""):
    hit = _clicked_cluster(pie_state, cl_order, label_to_cluster)
    if hit is not None:
        drill = hit
st.session_state["_trx_drill_sig"] = {"bar": sig_bar, "pie": sig_pie}
# klaster terpilih harus masih ada dalam tampilan; jika tidak, kosongkan
if drill is not None and drill not in cl_order:
    drill = None
st.session_state["trx_drill"] = drill

# ---- space drill-down: rincian kategori untuk klaster yang dipencet ----
drill_box = st.container()
with drill_box:
    if drill is None:
        st.markdown(
            '<div class="card" style="border-style:dashed;text-align:center;'
            'color:var(--text-dim);">Pilih sebuah klaster pada grafik di atas untuk '
            'menampilkan rincian kategori di sini.</div>', unsafe_allow_html=True)
    else:
        nm = short_map.get(drill, f"Klaster {drill}") if is_reco else f"Klaster {drill}"
        head_c1, head_c2 = st.columns([4, 1])
        head_c1.markdown(
            f'<div class="prof-head" style="margin-top:6px;">'
            f'<span class="cl-dot" style="background:{charts.cluster_color(drill)}"></span>'
            f'<strong>Rincian kategori — Klaster {drill}'
            f'{" · " + nm if is_reco else ""}</strong></div>', unsafe_allow_html=True)
        if head_c2.button("Tutup rincian", key="trx_drill_close"):
            st.session_state["trx_drill"] = None
            st.session_state["_trx_drill_sig"] = {"bar": "", "pie": ""}
            st.rerun()
        notas_in = set(view.loc[view["cluster"] == drill, "nota"])
        item_rows = trx.filter_valid_rows(df)
        item_rows = item_rows[item_rows["receipt_number"].isin(notas_in)]
        if "category" in item_rows.columns and len(item_rows):
            item_rows = item_rows.assign(category=item_rows["category"].fillna("(tak terkategori)"))
            dc = st.columns(2)
            with dc[0]:
                st.plotly_chart(
                    charts.bar_categories(item_rows, "Kategori per Item Terjual (kuantitas)",
                                          value="quantity", n=20, color_by_cluster=drill),
                    use_container_width=True)
            with dc[1]:
                st.plotly_chart(
                    charts.donut_category(item_rows, value="quantity"),
                    use_container_width=True)
        else:
            st.info("Rincian kategori tidak tersedia untuk klaster ini.")

# ---- profil segmen (hanya untuk kombinasi rekomendasi) ----
st.markdown('<div class="panel-title">Profil Segmen & Rekomendasi</div>',
            unsafe_allow_html=True)
if is_reco:
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
else:
    _md('<div class="card card-cream"><h3>Pelabelan segmen tidak tersedia</h3>'
        '<p>Kombinasi fitur yang dipilih <strong>bukan</strong> konfigurasi klaster terbaik '
        'yang ditetapkan pengembang, sehingga hasil hanya ditampilkan sebagai nomor klaster '
        'tanpa profil segmen maupun rekomendasi bisnis. Untuk memperoleh pelabelan segmen, '
        'kembalikan pilihan fitur ke rekomendasi penelitian (Nilai belanja + Rasio minuman + '
        'Ragam jenis item), lalu tekan Run model.</p></div>')

# ---- tabel hasil klaster (sertakan rincian item tiap nota) ----
st.markdown('<div class="panel-title">Data Hasil Klaster</div>', unsafe_allow_html=True)
items_map = trx.build_nota_items(df)
base_cols = ["nota", "cluster"]
if is_reco:
    base_cols.append("segmen")
base_cols += ["total_net", "total_qty", "n_item_unik",
              "qty_makanan", "qty_minuman", "rasio_minuman", "ada_alkohol", "jam"]
tbl = view[base_cols].copy()
tbl["rasio_minuman"] = tbl["rasio_minuman"].round(2)
tbl = tbl.merge(items_map, on="nota", how="left")
tbl["items"] = tbl["items"].fillna("")
tbl = tbl.sort_values(["cluster", "total_net"], ascending=[True, False])
# kolom 'items' diletakkan tepat setelah nota agar rincian isi nota mudah dibaca
order = ["nota", "items"] + [c for c in base_cols if c != "nota"]
tbl = tbl[order]
st.dataframe(tbl, use_container_width=True, height=420, hide_index=True,
             column_config={"items": st.column_config.TextColumn("items", width="large")})

download_button(tbl, "Unduh hasil klaster (CSV)", "klaster_transaksi.csv",
                key="dl_klaster_trx")
