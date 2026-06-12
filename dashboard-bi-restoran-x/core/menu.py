"""Rekayasa fitur tingkat menu, pemetaan makanan/minuman, skema fitur, dan profiling.
Pemetaan kategori mereproduksi pembagian pada penelitian (176 makanan, 148 minuman)."""
import numpy as np
import pandas as pd

# kategori minuman; sisanya (termasuk 'uncategorized') dianggap makanan
MINUMAN_CATS = {"alkohol", "cocktail", "juice / drinks", "soft drinks",
                "coffee based", "non coffee", "mocktail"}
EXCLUDE_CATS = {"complimentary", "refund"}

# K sesuai kesimpulan penelitian (skema utama)
THESIS_K = {"makanan": 3, "minuman": 5}

# nama skema -> (daftar fitur, pakai_profiling)
FEATURE_SCHEMES = {
    "Skema utama — Kuantitas & Harga (rekomendasi penelitian)": (["quantity", "avg_price"], True),
    "Alternatif — Volume & Pendapatan": (["quantity", "net_revenue"], False),
    "Alternatif — Popularitas & Frekuensi": (["quantity", "frequency"], False),
    "Alternatif — Harga & Ukuran Pesanan": (["avg_price", "units_per_order"], False),
}

FEATURE_LABEL = {
    "quantity": "Kuantitas", "avg_price": "Harga rata-rata",
    "net_revenue": "Pendapatan bersih", "frequency": "Frekuensi",
    "units_per_order": "Unit per pesanan", "gross_sales": "Penjualan kotor",
}


def assign_group(cat):
    if cat in EXCLUDE_CATS:
        return None
    if cat in MINUMAN_CATS:
        return "minuman"
    return "makanan"


def build_menu_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agregasi data transaksi-item menjadi fitur per menu (mirip *_raw_feat)."""
    d = df.copy()
    cat = d.groupby("items")["category"].agg(
        lambda s: s.mode().iloc[0] if len(s.mode()) else None)
    g = d.groupby("items")
    out = pd.DataFrame({
        "quantity": g["quantity"].sum(),
        "frequency": g["receipt_number"].nunique() if "receipt_number" in d.columns else g.size(),
        "net_revenue": g["net_sales"].sum(),
        "gross_sales": g["gross_sales"].sum(),
        "avg_price": g["item_price"].mean() if "item_price" in d.columns else g["net_sales"].mean(),
    })
    out["units_per_order"] = (out["quantity"] / out["frequency"]).replace([np.inf, -np.inf], np.nan)
    out["category"] = cat
    out["grup"] = out["category"].map(assign_group)
    return out.reset_index()


TIER_NAMES = ["Bintang", "Andalan", "Reguler", "Musiman", "Pelengkap", "Ekor panjang"]


def profile_clusters(menu_df: pd.DataFrame):
    """Label profil yang dijamin berbeda per klaster: tingkat popularitas (urut
    berdasarkan kuantitas) ditambah keterangan harga (premium/ekonomis vs median)."""
    d = menu_df
    med_p = d["avg_price"].median()
    means = d.groupby("cluster").agg(q=("quantity", "mean"), p=("avg_price", "mean"))
    order = means["q"].sort_values(ascending=False).index.tolist()
    label = {}
    for i, c in enumerate(order):
        tier = TIER_NAMES[min(i, len(TIER_NAMES) - 1)]
        price = "premium" if means.loc[c, "p"] >= med_p else "ekonomis"
        label[c] = f"{tier} \u00b7 {price}"
    return d["cluster"].map(label), label
