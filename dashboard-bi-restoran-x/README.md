# Dashboard BI Restoran X

Business Intelligence Dashboard untuk segmentasi penjualan menggunakan **K-Means++**.
Skripsi SAKTI — Informatika, Universitas Udayana, 2026.

## Menjalankan

```bash
pip install -r requirements.txt
streamlit run app.py
```

Dashboard terbuka di `http://localhost:8501`.

## Struktur Proyek

```
dashboard-bi-restoran-x/
├── Home.py                  # entry point + navigasi (st.navigation)
├── app_pages/               # isi tiap halaman
│   ├── p1_beranda.py        # 1. Beranda
│   ├── p2_lihat_dataset.py  # 2. Lihat Dataset (pemilik)
│   ├── p3_klaster_menu.py   # 3. Klaster Menu (pemilik)
│   ├── p4_klaster_transaksi.py  # 4. Klaster Transaksi (lanjutan)
│   ├── p5_dev_menu.py       # 5. Developer · Menu (teknis)
│   └── p6_dev_transaksi.py  # 6. Developer · Transaksi (lanjutan)
├── core/                    # logika bersama
│   ├── ui.py                # injeksi CSS, brand, komponen UI
│   ├── data.py              # baca CSV/XLSX, validasi, unduh
│   └── cluster.py           # K-Means / K-Means++, metrik, filter klaster
├── assets/
│   ├── style.css            # design token (warna, tipografi, komponen)
│   └── streamlit.css        # override chrome Streamlit
├── data/
│   └── data_master_2023_2024_final.csv   # dataset master bawaan
└── .streamlit/config.toml   # tema dark + olive
```

## Tema

Seluruh variabel desain dipusatkan di `assets/style.css` (`:root { ... }`).
Tema gelap (hitam-arang) dengan aksen olive/sage. Untuk mengubah warna,
cukup ubah variabel di blok `:root`.

## Format Data Masukan

Dataset yang diunggah harus mengikuti struktur **hasil ekspor langsung POS**
(master final), berformat `.csv` atau `.xlsx`. Kolom inti yang wajib ada:
`items, quantity, net_sales, gross_sales, category`.

## Status

Modul tingkat menu (Beranda, Lihat Dataset, Klaster Menu, Developer · Menu)
dikerjakan terlebih dahulu. Modul tingkat transaksi dikembangkan pada tahap lanjutan.
