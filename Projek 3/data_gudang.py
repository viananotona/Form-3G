import os
import requests
from flask import Flask, render_template

# =========================================================================
# 1. KONFIGURASI HARGA DAN API
# =========================================================================

# Inisialisasi Objek Aplikasi Flask
app = Flask(__name__)

# Mengambil URL SheetDB dari Environment Variable Render.
# Ini penting untuk keamanan dan deployment!
SHEETDB_URL = os.environ.get("SHEETDB_URL") 
# Jika Anda menjalankan secara lokal, Anda bisa mengganti baris di atas dengan:
# SHEETDB_URL = "https://sheetdb.io/api/v1/GANTI_DENGAN_API_KEY_ANDA" 
# dan pastikan Anda menginstal python-dotenv untuk testing lokal.

# Harga Beli & Jual yang Ditetapkan di Python (Fixed Data)
HARGA_PRODUK = {
    "kopi": {
        "beli": 10000, 
        "jual": 12000 
    },
    "gula": {
        "beli": 13000,
        "jual": 15000
    }
}

# =========================================================================
# 2. FUNGSI UTAMA: FETCH DATA & PERHITUNGAN
# =========================================================================

@app.route('/')
def hitung_laporan():
    """
    Metode utama yang menangani permintaan web, mengambil data dari API, 
    melakukan perhitungan, dan menampilkan hasilnya di template HTML.
    """
    
    # ⚠️ Cek Keberadaan URL untuk menghindari error 500 saat deployment
    if not SHEETDB_URL:
        return "<h1>Error Konfigurasi</h1><p>Variabel lingkungan SHEETDB_URL belum diatur di Render.</p>", 500
        
    try:
        # A. Fetch Data dari SheetDB
        response = requests.get(SHEETDB_URL)
        response.raise_for_status() # Cek status HTTP 4xx/5xx
        data_transaksi = response.json()
    except requests.exceptions.RequestException as e:
        # Error koneksi
        return f"<h1>Error Koneksi API: {e}</h1><p>Pastikan SheetDB URL Anda sudah benar dan layanan aktif.</p>", 500
    except ValueError:
        # Error format JSON
        return "<h1>Error: Respons dari SheetDB bukan format JSON yang valid.</h1>", 500

    
    # B. Inisialisasi Akumulator (Menyimpan Total Sementara)
    total_stok_masuk = 0
    total_stok_keluar = 0
    total_harga_beli = 0 
    total_harga_jual = 0 
    
    # C. Loop Transaksi & Akumulasi Nilai
    for transaksi in data_transaksi:
        
        # Ambil data dari kolom Sheets dan konversi ke huruf kecil agar konsisten
        nama_barang = transaksi.get("nama barang", "").lower() 
        jenis_stok = transaksi.get("jenis", "").lower()
        
        try:
            # Ambil Jumlah, pastikan berupa integer. Gunakan 0 jika gagal konversi.
            jumlah = int(transaksi.get("jumlah", 0))
        except ValueError:
            continue 

        # Logika Bisnis: Cek apakah barang ada dalam daftar harga kita dan jumlahnya valid
        if nama_barang in HARGA_PRODUK and jumlah > 0:
            
            harga_beli = HARGA_PRODUK[nama_barang]["beli"]
            harga_jual = HARGA_PRODUK[nama_barang]["jual"]
            
            if jenis_stok == "masuk":
                # Transaksi Masuk = Beli (Mempengaruhi Modal Beli)
                total_stok_masuk += jumlah
                total_harga_beli += harga_beli * jumlah 
                
            elif jenis_stok == "keluar":
                # Transaksi Keluar = Jual (Mempengaruhi Total Revenue Jual)
                total_stok_keluar += jumlah
                total_harga_jual += harga_jual * jumlah
                
    # D. Perhitungan Akhir
    # Selisih = Total Harga Jual - Total Harga Beli (Modal)
    selisih_untung_rugi = total_harga_jual - total_harga_beli 
    
    # Menentukan Status
    if selisih_untung_rugi > 0:
        status = "Untung"
    elif selisih_untung_rugi < 0:
        status = "Rugi"
    else:
        status = "Impase (Break Even)"
        
    # E. Kumpulkan Hasil dalam Dictionary untuk dikirim ke HTML
    laporan = {
        "stok_masuk": total_stok_masuk,
        "stok_keluar": total_stok_keluar,
        "harga_beli": total_harga_beli,
        "harga_jual": total_harga_jual,
        "selisih": selisih_untung_rugi,
        "status": status
    }
    
    # F. Tampilkan ke Web menggunakan template laporan.html
    return render_template('laporan.html', data=laporan)

# CATATAN: Blok if __name__ == '__main__': dihilangkan. 
# Aplikasi dijalankan oleh Gunicorn (Procfile) di Render.
