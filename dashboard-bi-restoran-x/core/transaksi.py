"""Rekayasa fitur tingkat transaksi (per nota), praproses, dan profiling segmen.

Modul ini sejajar dengan core.menu, tetapi bekerja pada tingkat nota: master
diagregasi per ``receipt_number`` menjadi satu baris per nota. Seluruh skema
mereproduksi Notebook 04 (Pemodelan Klaster Transaksi):

* Fitur klaster  : total_net, rasio_minuman, n_item_unik (terpilih via uji VIF, semua < 5)
* Praproses      : winsorization persentil ke-99 (total_net & n_item_unik) -> Z-score
* Algoritme      : K-Means++ (n_init=10, random_state=42)
* Jumlah klaster : K = 5 (Silhouette tertinggi @ K=5, diselaraskan DBI terendah)
* Profiling      : komposisi (rasio_minuman) lebih dulu, lalu besaran belanja
"""
import numpy as np
import pandas as pd

# Kategori minuman — identik dengan Notebook 04 (sejajar core.menu.MINUMAN_CATS).
# Seluruh kategori lain (termasuk makanan & tak terkategori) dihitung sebagai makanan.
GRUP_MINUMAN = {"soft drinks", "alkohol", "juice / drinks", "coffee based",
                "cocktail", "mocktail", "non coffee"}

# Fitur final tingkat transaksi (urutan dipertahankan: R=total_net, G=rasio_minuman, B=n_item_unik).
TRX_FEATURES = ["total_net", "rasio_minuman", "n_item_unik"]
# Jumlah klaster sesuai kesimpulan Notebook 04.
TRX_K = 5
# Fitur kontinu yang diwinsor (rasio_minuman sudah berada pada skala [0,1], tidak diwinsor).
WINSOR_FEATURES = ["total_net", "n_item_unik"]
# Persentil winsorization (Notebook 04 menggunakan p99 pada tingkat transaksi).
CAP_PCT = 0.99

FEATURE_LABEL = {
    "total_net": "Nilai belanja (net)",
    "rasio_minuman": "Rasio minuman",
    "n_item_unik": "Ragam jenis item",
    "total_qty": "Total item",
    "total_gross": "Penjualan kotor",
    "qty_makanan": "Item makanan",
    "qty_minuman": "Item minuman",
    "jam": "Jam transaksi",
}


def filter_valid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Saring baris sah menuju data tingkat transaksi (sesuai Notebook 04):
    hanya pembayaran (payment), buang pemberian gratis (complimentary, Rp0), dan
    buang entri 'custom amount' (open-amount kasir). Penyaringan bersifat defensif:
    kolom yang tidak tersedia pada unggahan dilewati tanpa menggugurkan proses."""
    d = df.copy()
    if "event_type" in d.columns:
        d = d[d["event_type"] == "payment"]
    if "category" in d.columns:
        d = d[d["category"] != "complimentary"]
    if "items" in d.columns:
        custom = d["items"].astype(str).str.lower().str.contains("custom amount", na=False)
        d = d[~custom]
    return d.copy()


def build_transaksi_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agregasi data transaksi-item menjadi fitur per nota (per receipt_number),
    persis Notebook 04. Mengembalikan satu baris per nota beserta fitur dasar,
    fitur komposisi (rasio_minuman), penanda alkohol, dan jam transaksi."""
    d = filter_valid_rows(df)
    for c in ("quantity", "net_sales", "gross_sales"):
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    if "gross_sales" not in d.columns:
        d["gross_sales"] = d["net_sales"]
    cat = d["category"] if "category" in d.columns else pd.Series("", index=d.index)
    waktu = pd.to_datetime(d["datetime"], errors="coerce") if "datetime" in d.columns \
        else pd.Series(pd.NaT, index=d.index)

    d = d.assign(
        _waktu=waktu,
        q_minuman=np.where(cat.isin(GRUP_MINUMAN), d["quantity"], 0),
        q_makanan=np.where(~cat.isin(GRUP_MINUMAN), d["quantity"], 0),
        is_alkohol=(cat == "alkohol").astype(int),
    )
    g = d.groupby("receipt_number")
    nota = pd.DataFrame({
        "total_qty": g["quantity"].sum(),
        "n_item_unik": g["items"].nunique(),
        "total_net": g["net_sales"].sum(),
        "total_gross": g["gross_sales"].sum(),
        "qty_makanan": g["q_makanan"].sum(),
        "qty_minuman": g["q_minuman"].sum(),
        "ada_alkohol": g["is_alkohol"].max(),
        "waktu": g["_waktu"].min(),
    }).reset_index().rename(columns={"receipt_number": "nota"})
    nota = nota[nota["total_qty"] > 0].reset_index(drop=True)
    nota["jam"] = nota["waktu"].dt.hour
    nota["rasio_minuman"] = (nota["qty_minuman"] / nota["total_qty"]).replace(
        [np.inf, -np.inf], np.nan).fillna(0)
    return nota


def run_transaksi_clustering(nota_df: pd.DataFrame, k: int = TRX_K,
                             algo: str = "kmeans++", seed: int = 42):
    """Pipeline lengkap tingkat transaksi: winsorize p99 (total_net & n_item_unik)
    -> Z-score -> K-Means(++) dengan K. Label klaster diturunkan dari ruang fitur
    yang telah diwinsor & distandardisasi, lalu ditempelkan pada data ASLI
    (nilai tak diwinsor) agar profil & tabel mencerminkan nilai sebenarnya.

    Mengembalikan (nota_berlabel, hasil_klastering, Xz, scaler)."""
    from core import cluster as cl  # pakai ulang core.cluster (winsorize/standardize/run_clustering)

    d = nota_df.copy()
    for c in WINSOR_FEATURES:
        d[c] = cl.winsorize(d[c].astype(float), CAP_PCT)
    Xz, scaler = cl.standardize(d[TRX_FEATURES].astype(float))
    res = cl.run_clustering(Xz, k, algo=algo, seed=seed)

    out = nota_df.copy()
    out["cluster"] = res["labels"]
    return out, res, Xz, scaler


def plot_axis(series: pd.Series, feat: str) -> pd.Series:
    """Nilai untuk sumbu scatter: fitur kontinu dibatasi p99 (selaras ruang fitur
    yang dipakai model), sedangkan rasio_minuman dibiarkan apa adanya [0,1]."""
    from core import cluster as cl
    if feat in WINSOR_FEATURES:
        return cl.winsorize(series.astype(float), CAP_PCT)
    return series.astype(float)


# ---------------------------------------------------------------------------
# Profiling segmen — mereproduksi fungsi beri_label & REKO pada Notebook 04.
# ---------------------------------------------------------------------------
SEG_NONGKRONG = "Nongkrong / Minum (hampir murni minuman)"
SEG_BRUNCH = "Makan Saja / Brunch (hampir murni makanan)"
# urut menurun berdasarkan rata belanja untuk klaster campuran
SEG_MIXED = ["Rombongan / Acara (besar & beragam)",
             "Makan Lengkap (pelanggan inti)",
             "Reguler Menengah",
             "Campuran"]

REKO = {
    SEG_NONGKRONG: "Kerumunan bar/kafe: jalankan happy hour & promo minuman; cross-sell camilan/bar food.",
    SEG_BRUNCH: "Peluang upsell minuman terbesar: bundling kopi/jus dengan set makanan.",
    "Rombongan / Acara (besar & beragam)": "Segmen bernilai tertinggi per kunjungan: paket grup, reservasi, jaga stok beer & menu populer.",
    "Makan Lengkap (pelanggan inti)": "Tulang punggung omzet: jaga kualitas & variasi, dorong upsell dessert/minuman.",
    "Reguler Menengah": "Volume harian: jaga kecepatan layanan & tawarkan paket hemat untuk menaikkan nilai nota.",
    "Campuran": "Tinjau lebih lanjut sesuai konteks.",
}


def profile_clusters(nota_df: pd.DataFrame):
    """Label segmen objektif per klaster (reproduksi Notebook 04): komposisi
    (rasio_minuman >= 0.85 atau <= 0.15) ditetapkan lebih dahulu, sisanya
    (campuran) diurut menurun berdasarkan rata belanja. Label diturunkan dari
    KARAKTERISTIK klaster — bukan nomor klaster — sehingga tetap sahih bila data
    yang diunggah berbeda.

    Mengembalikan (Series segmen per baris, dict segmen per klaster, dict rekomendasi)."""
    prof = nota_df.groupby("cluster").agg(
        rata_belanja=("total_net", "mean"),
        rasio_minuman=("rasio_minuman", "mean")).reset_index()
    lab, mixed = {}, []
    for _, r in prof.iterrows():
        c = int(r["cluster"])
        if r["rasio_minuman"] >= 0.85:
            lab[c] = SEG_NONGKRONG
        elif r["rasio_minuman"] <= 0.15:
            lab[c] = SEG_BRUNCH
        else:
            mixed.append(c)
    urut = sorted(mixed, key=lambda c: float(
        prof.loc[prof["cluster"] == c, "rata_belanja"].iloc[0]), reverse=True)
    for i, c in enumerate(urut):
        lab[c] = SEG_MIXED[min(i, len(SEG_MIXED) - 1)]
    reko = {c: REKO.get(lab[c], "") for c in lab}
    return nota_df["cluster"].map(lab), lab, reko


def short_label(name: str) -> str:
    """Versi ringkas nama segmen untuk chip/legenda (buang keterangan dalam kurung)."""
    return name.split(" (")[0].strip()


def cluster_profile_table(nota_df: pd.DataFrame, seg_map: dict,
                          reko_map: dict = None) -> pd.DataFrame:
    """Ringkasan profil per klaster untuk ditampilkan/diekspor: jumlah & persentase
    nota, rata belanja, ragam item, rasio minuman, persentase beralkohol, jam median,
    kontribusi pendapatan, segmen, dan (opsional) rekomendasi BI."""
    tot_rev = nota_df["total_net"].sum()
    n_tot = len(nota_df)
    prof = nota_df.groupby("cluster").agg(
        jumlah_nota=("nota", "size"),
        rata_belanja=("total_net", "mean"),
        rata_item=("total_qty", "mean"),
        rata_jenis=("n_item_unik", "mean"),
        rasio_minuman=("rasio_minuman", "mean"),
        pct_beralkohol=("ada_alkohol", lambda s: round(s.mean() * 100, 1)),
        total_pendapatan=("total_net", "sum"),
        jam_median=("jam", "median")).reset_index()
    prof["pct_nota"] = (prof["jumlah_nota"] / n_tot * 100).round(1)
    prof["pct_pendapatan"] = (prof["total_pendapatan"] / tot_rev * 100).round(1)
    prof["segmen"] = prof["cluster"].map(seg_map)
    if reko_map is not None:
        prof["rekomendasi_BI"] = prof["cluster"].map(reko_map)
    for c in ("rata_belanja", "rata_item", "rata_jenis", "rasio_minuman"):
        prof[c] = prof[c].round(2)
    return prof.sort_values("pct_pendapatan", ascending=False).reset_index(drop=True)
