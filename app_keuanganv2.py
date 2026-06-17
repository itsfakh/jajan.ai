import json
import streamlit as st
import pandas as pd
from PIL import Image
from google import genai
from google.genai import types
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# ==================================
# PAGE CONFIG & CSS
# ==================================
st.set_page_config(page_title="ScanStruk AI V2", page_icon="🧾", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #f8fafc, #e0f2fe); }
.hero { background: linear-gradient(90deg, #0284c7, #38bdf8); padding: 30px; border-radius: 25px; text-align: center; color: white; margin-bottom: 25px; box-shadow: 0px 4px 20px rgba(0,0,0,0.1); }
.card { background: white; color: #1e293b !important; padding: 20px; border-radius: 20px; box-shadow: 0px 4px 20px rgba(0,0,0,0.05); margin-bottom: 20px; }
.metric-today { background: linear-gradient(135deg, #fef2f2, #fecaca); padding: 20px; border-radius: 20px; text-align: center; border: 2px dashed #ef4444; margin-bottom: 15px; }
.metric-month { background: linear-gradient(135deg, #eff6ff, #bfdbfe); padding: 20px; border-radius: 20px; text-align: center; border: 2px dashed #3b82f6; margin-bottom: 15px; }
.metric-today h4 { color: #991b1b !important; margin: 0; font-size: 16px;}
.metric-today h2 { color: #b91c1c !important; margin: 5px 0 0 0; font-size: 28px; }
.metric-month h4 { color: #1e3a8a !important; margin: 0; font-size: 16px;}
.metric-month h2 { color: #1d4ed8 !important; margin: 5px 0 0 0; font-size: 28px; }
.stButton > button { width: 100%; height: 55px; border-radius: 15px; border: none; background: #0284c7; color: white; font-size: 18px; font-weight: bold; }
.stButton > button:hover { background: #0369a1; color: white; }
label, p, span, small, div, li { color: #1e293b !important; }
</style>
""", unsafe_allow_html=True)

# ==================================
# API KEY & KONEKSI GOOGLE SHEETS
# ==================================
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("⚠️ GEMINI_API_KEY tidak ditemukan.")
    st.stop()

try:
    kunci_json = json.loads(st.secrets["GCP_CREDENTIALS"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(kunci_json, scopes=scopes)
    client_gs = gspread.authorize(creds)
    
    # ⚠️ PENTING: Paste link URL Google Sheets "Database Keuangan AI" kamu di sini!
    sheet = client_gs.open_by_url("PASTE_LINK_GOOGLE_SHEETS_KEUANGAN_DI_SINI").sheet1 
except Exception as e:
    st.error(f"⚠️ Gagal terhubung ke Google Sheets. Error: {e}")
    st.stop()

# ==================================
# SIDEBAR: AKSES PENGGUNA
# ==================================
st.sidebar.markdown("## 👤 Akses Pengguna")
input_nama = st.sidebar.text_input("Username (Ketik & Enter)", value="USER_BARU")
nama_pengguna = input_nama.upper().strip()

# ==================================
# BACA DATABASE BERDASARKAN USERNAME
# ==================================
waktu_sekarang_dt = datetime.utcnow() + timedelta(hours=7)
waktu_hari_ini = waktu_sekarang_dt.strftime("%Y-%m-%d")
bulan_ini_str = waktu_sekarang_dt.strftime("%Y-%m")

data_user_semua = []
data_user_bulan_ini = []
total_hari_ini = 0
total_bulan_ini = 0
daftar_kategori = ["Makanan & Minuman", "Transportasi", "Kebutuhan Kuliah/Kos", "Tagihan & Pulsa/Internet", "Hiburan & Game", "Tabungan & Investasi", "Lainnya"]

try:
    semua_data = sheet.get_all_values()
    for row in semua_data[1:]:
        # Pastikan baris memiliki minimal 5 kolom (ada username-nya) dan cocok dengan nama yang diketik
        if len(row) >= 5 and row[4] == nama_pengguna:
            data_user_semua.append(row)
            tanggal_row = row[0]
            
            try: nominal = int(row[3])
            except: nominal = 0
            
            # Hitung total hari ini
            if tanggal_row == waktu_hari_ini:
                total_hari_ini += nominal
            
            # Hitung total bulan ini & kumpulkan datanya untuk grafik
            if tanggal_row.startswith(bulan_ini_str):
                total_bulan_ini += nominal
                data_user_bulan_ini.append(row)
                
except Exception as e:
    st.warning("Belum ada data dasar di database.")

# Olah Data untuk Grafik (Hanya data bulan ini saja agar grafik relevan)
df_kategori = pd.DataFrame()
if len(data_user_bulan_ini) > 0:
    df = pd.DataFrame(data_user_bulan_ini, columns=["Tanggal", "Keterangan", "Kategori", "Nominal", "Username"])
    df['Nominal'] = pd.to_numeric(df['Nominal'], errors='coerce').fillna(0)
    df_kat = df.groupby('Kategori')['Nominal'].sum().reset_index()
    df_kategori = df_kat.set_index('Kategori')

# ==================================
# HEADER & DASHBOARD KEUANGAN
# ==================================
st.markdown('<div class="hero"><h1>🧾 ScanStruk AI V2</h1><p style="font-size:18px;">Manajer Keuangan Cerdas • Multi-User System</p></div>', unsafe_allow_html=True)

col_m1, col_m2, col_chart = st.columns([1, 1, 2])

with col_m1:
    st.markdown(
        f"""
        <div class="metric-today" style="height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <h4>💸 Keluar Hari Ini</h4>
            <h2>Rp {int(total_hari_ini):,}</h2>
        </div>
        """, unsafe_allow_html=True
    )

with col_m2:
    st.markdown(
        f"""
        <div class="metric-month" style="height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <h4>📆 Keluar Bulan Ini</h4>
            <h2>Rp {int(total_bulan_ini):,}</h2>
        </div>
        """, unsafe_allow_html=True
    )

with col_chart:
    st.markdown("<div class='card' style='text-align: center; margin-bottom: 0; padding: 10px;'><b>📊 Distribusi Dana Bulan Ini</b>", unsafe_allow_html=True)
    if not df_kategori.empty:
        st.bar_chart(df_kategori, height=150)
    else:
        st.info("Belum ada transaksi bulan ini.")
    st.markdown("</div>", unsafe_allow_html=True)

# ==================================
# AREA INPUT: HYBRID SYSTEM (MANUAL & AI)
# ==================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f'<div class="card"><h3>📥 Tambah Transaksi ({nama_pengguna})</h3></div>', unsafe_allow_html=True)

tab_manual, tab_ai = st.tabs(["📝 Catat Manual (Tanpa Struk)", "📷 Pindai Struk / Bukti Transfer (Otomatis)"])

with tab_manual:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("form_pencatatan_manual", clear_on_submit=True):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            tgl_manual = st.date_input("Tanggal Transaksi", value=datetime.utcnow() + timedelta(hours=7))
            ket_manual = st.text_input("Keterangan Pengeluaran", placeholder="Contoh: Jajan Bakso, Bayar Parkir Pasar")
        with col_m2:
            kat_manual = st.selectbox("Pilih Kategori", daftar_kategori)
            nom_manual = st.number_input("Nominal Pengeluaran (Rp)", min_value=0, step=500, value=0)
            
        btn_simpan_manual = st.form_submit_button("💾 Simpan Catatan")
        
        if btn_simpan_manual:
            if ket_manual.strip() != "" and nom_manual > 0:
                format_tgl = tgl_manual.strftime("%Y-%m-%d")
                # FITUR BARU: Menyelipkan nama_pengguna ke kolom E (kolom ke-5)
                sheet.append_row([format_tgl, ket_manual.strip(), kat_manual, int(nom_manual), nama_pengguna])
                st.success(f"✅ Berhasil mencatat manual: {ket_manual} (Rp {int(nom_manual):,})!")
                st.rerun()
            else:
                st.warning("⚠️ Gagal menyimpan. Harap isi keterangan pengeluaran dan nominal uang dengan benar!")

with tab_ai:
    st.markdown("<br>", unsafe_allow_html=True)
    left_col, right_col = st.columns([1, 1])
    
    with left_col:
        camera_image = st.camera_input("Ambil Foto Struk")
        uploaded_file = st.file_uploader("Atau Unggah Gambar Bukti", type=["jpg", "jpeg", "png"])
    image_file = camera_image if camera_image else uploaded_file
    
    with right_col:
        if image_file:
            st.image(Image.open(image_file), use_container_width=True)
        else:
            st.info("Kamera aktif atau unggahan gambar akan muncul pratinjaunya di sini.")
            
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔍 Jalankan Pemindaian AI"):
        if image_file:
            with st.spinner("🤖 AI sedang membaca struktur teks dan nominal..."):
                proses_image = Image.open(image_file)
                proses_image.thumbnail((1000, 1000))
                
                prompt = """
                Anda adalah asisten keuangan pribadi yang sangat teliti. Baca struk kasir atau screenshot bukti transaksi ini.
                Ekstrak informasi berikut dengan akurat:
                1. "tanggal": Ambil tanggal transaksi di gambar (format YYYY-MM-DD). Jika tidak ada, gunakan tanggal hari ini.
                2. "keterangan": Nama toko, nama *merchant*, atau rincian transaksi singkat (misal: Indomaret, Mie Ayam, Top Up E-Wallet, dll).
                3. "kategori": Pilih SATU kategori yang paling cocok dari daftar ini: [Makanan & Minuman, Transportasi, Kebutuhan Kuliah/Kos, Tagihan & Pulsa/Internet, Hiburan & Game, Tabungan & Investasi, Lainnya].
                4. "nominal": Total akhir uang yang dikeluarkan. Tulis HANYA ANGKA MURNI tanpa titik, tanpa koma, tanpa Rp (contoh: 25000).

                Balas HANYA menggunakan format JSON seperti ini:
                {"tanggal": "2023-10-25", "keterangan": "Beli Nasi Goreng", "kategori": "Makanan & Minuman", "nominal": 25000}
                """
                
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash", 
                        contents=[prompt, proses_image],
                        config=types.GenerateContentConfig(temperature=0.0)
                    )
                    
                    result_text = response.text.replace("```json", "").replace("
```", "").strip()
                    data = json.loads(result_text)
                    
                    tanggal = data.get("tanggal", datetime.utcnow().strftime("%Y-%m-%d"))
                    keterangan = data.get("keterangan", "Pengeluaran Tak Diketahui")
                    kategori = data.get("kategori", "Lainnya")
                    try: nominal = int(data.get("nominal", 0))
                    except: nominal = 0
                    
                    # FITUR BARU: Menyelipkan nama_pengguna ke kolom E (kolom ke-5)
                    sheet.append_row([tanggal, keterangan, kategori, nominal, nama_pengguna])
                    st.success(f"✅ AI Berhasil mencatat: {keterangan} (Rp {nominal:,})!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Gagal memproses gambar. Detail kendala: {e}")
        else:
            st.warning("⚠️ Sediakan dokumen foto struk atau screenshot transaksi terlebih dahulu!")

# ==================================
# TABEL RIWAYAT TRANSAKSI TERAKHIR
# ==================================
if len(data_user_semua) > 0:
    st.markdown("---")
    st.markdown(f"### 📋 10 Transaksi Terakhir ({nama_pengguna})")
    # Membalik array agar yang terbaru di atas, lalu ambil 10 teratas
    data_terbalik = data_user_semua[::-1][:10] 
    
    for item in data_terbalik:
        try: nominal_rupiah = f"Rp {int(item[3]):,}"
        except: nominal_rupiah = item[3]
        
        st.markdown(f"🗓️ **{item[0]}** | {item[1]} — 💳 **{nominal_rupiah}** *({item[2]})*")
