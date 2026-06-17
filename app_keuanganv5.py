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
st.set_page_config(page_title="ScanStruk AI V5", page_icon="🧾", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #f8fafc, #e0f2fe); }
.hero { background: linear-gradient(90deg, #0284c7, #38bdf8); padding: 30px; border-radius: 25px; text-align: center; color: white; margin-bottom: 25px; box-shadow: 0px 4px 20px rgba(0,0,0,0.1); }
.card { background: white; color: #1e293b !important; padding: 20px; border-radius: 20px; box-shadow: 0px 4px 20px rgba(0,0,0,0.05); margin-bottom: 20px; }
.target-card { background: linear-gradient(135deg, #e0f2fe, #bae6fd); padding: 20px; border-radius: 20px; text-align: center; border: 2px dashed #0284c7; margin-bottom: 20px; box-shadow: 0px 4px 15px rgba(0,0,0,0.05); }
.target-card h2 { color: #0369a1 !important; margin: 0; font-size: 32px; font-weight: bold; }
.metric-today { background: linear-gradient(135deg, #fef2f2, #fecaca); padding: 15px; border-radius: 20px; text-align: center; border: 2px dashed #ef4444; }
.metric-month { background: linear-gradient(135deg, #eff6ff, #bfdbfe); padding: 15px; border-radius: 20px; text-align: center; border: 2px dashed #3b82f6; }
.metric-income { background: linear-gradient(135deg, #f0fdf4, #bbf7d0); padding: 15px; border-radius: 20px; text-align: center; border: 2px dashed #22c55e); }
.metric-today h4 { color: #991b1b !important; margin: 0; font-size: 14px;}
.metric-today h2 { color: #b91c1c !important; margin: 5px 0 0 0; font-size: 24px; }
.metric-month h4 { color: #1e3a8a !important; margin: 0; font-size: 14px;}
.metric-month h2 { color: #1d4ed8 !important; margin: 5px 0 0 0; font-size: 24px; }
.metric-income h4 { color: #166534 !important; margin: 0; font-size: 14px;}
.metric-income h2 { color: #15803d !important; margin: 5px 0 0 0; font-size: 24px; }
.stButton > button { width: 100%; height: 55px; border-radius: 15px; border: none; background: #0284c7; color: white; font-size: 18px; font-weight: bold; }
.stButton > button:hover { background: #0369a1; color: white; }
label, p, span, small, div, li { color: #1e293b !important; }
.preview-box { background-color: #fef08a; border-left: 5px solid #eab308; padding: 20px; border-radius: 15px; margin-top: 15px; }
</style>
""", unsafe_allow_html=True)

# ==================================
# INITIALIZE SESSION STATE FOR AI PREVIEW
# ==================================
if "ai_preview_data" not in st.session_state:
    st.session_state.ai_preview_data = None

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
    
    gs_file = client_gs.open_by_url("https://docs.google.com/spreadsheets/d/1_72E-3eepzNO2dJRIiOFb1xWc64bu_4n44AivjgEbXQ/edit?gid=0#gid=0")
    sheet_riwayat = gs_file.sheet1 
    sheet_profil = gs_file.worksheet("Profil")
except Exception as e:
    st.error(f"⚠️ Gagal terhubung ke Google Sheets. Pastikan ada tab bernama 'Profil'. Error: {e}")
    st.stop()

# ==================================
# SIDEBAR: AKSES PENGGUNA & BUDGET
# ==================================
st.sidebar.markdown("## 👤 Akses Pengguna")
input_nama = st.sidebar.text_input("Username (Ketik & Enter)", value="USER_BARU")
nama_pengguna = input_nama.upper().strip()

waktu_sekarang_dt = datetime.utcnow() + timedelta(hours=7)
waktu_hari_ini = waktu_sekarang_dt.strftime("%Y-%m-%d")
bulan_ini_str = waktu_sekarang_dt.strftime("%Y-%m")

profil_values = sheet_profil.get_all_values()
user_row_index = None
saved_budget = 2000000 

for i, row in enumerate(profil_values):
    if i > 0 and len(row) >= 2 and row[0] == nama_pengguna:
        saved_budget = int(row[1])
        user_row_index = i + 1
        break

st.sidebar.markdown("---")
st.sidebar.markdown("## 🎯 Manajemen Anggaran")

if f"edit_budget_{nama_pengguna}" not in st.session_state:
    st.session_state[f"edit_budget_{nama_pengguna}"] = False

if user_row_index and not st.session_state[f"edit_budget_{nama_pengguna}"]:
    st.sidebar.success(f"🔒 Anggaran Tersimpan")
    st.sidebar.metric("Batas Bulanan Kamu:", f"Rp {saved_budget:,}")
    if st.sidebar.button("✏️ Edit Batas Anggaran"):
        st.session_state[f"edit_budget_{nama_pengguna}"] = True
        st.rerun()
    target_anggaran = saved_budget
else:
    target_anggaran = st.sidebar.number_input("Batas Anggaran Bulanan (Rp)", min_value=0, value=saved_budget, step=50000)
    if st.sidebar.button("💾 Simpan Anggaran ke Database"):
        with st.spinner("Menyimpan..."):
            if user_row_index:
                sheet_profil.update_cell(user_row_index, 2, int(target_anggaran))
            else:
                sheet_profil.append_row([nama_pengguna, int(target_anggaran)])
            st.session_state[f"edit_budget_{nama_pengguna}"] = False
            st.rerun()

# ==================================
# BACA DATABASE & LOGIKA PEMASUKAN VS PENGELUARAN (INOVASI 2)
# ==================================
data_user_semua = []
data_user_bulan_ini = []
total_hari_ini_keluar = 0
total_bulan_ini_keluar = 0
total_bulan_ini_masuk = 0 # Menyimpan total pendapatan bulan ini
baris_terakhir_user = None 

# Tambahkan "Pemasukan" ke dalam daftar pilihan kategori resmi
daftar_kategori = ["Makanan & Minuman", "Transportasi", "Kebutuhan Kuliah/Kos", "Tagihan & Pulsa/Internet", "Hiburan & Game", "Tabungan & Investasi", "Pemasukan (Gaji/Uang Saku)", "Lainnya"]

try:
    semua_data = sheet_riwayat.get_all_values()
    for index, row in enumerate(semua_data):
        if index == 0: continue
        if len(row) >= 5 and row[4] == nama_pengguna:
            data_user_semua.append(row)
            tanggal_row = str(row[0]).strip()
            kategori_row = row[2]
            baris_terakhir_user = index + 1
            
            try: 
                nom_bersih = str(row[3]).replace("Rp", "").replace(".", "").replace(",", "").strip()
                nominal = int(nom_bersih)
            except: 
                nominal = 0
            
            # Memisahkan perhitungan matematis antara pengeluaran dan pemasukan
            if kategori_row == "Pemasukan (Gaji/Uang Saku)":
                if tanggal_row.startswith(bulan_ini_str):
                    total_bulan_ini_masuk += nominal
            else:
                if tanggal_row == waktu_hari_ini:
                    total_hari_ini_keluar += nominal
                if tanggal_row.startswith(bulan_ini_str):
                    total_bulan_ini_keluar += nominal
                    data_user_bulan_ini.append(row)
                
except Exception as e:
    st.warning("Belum ada data dasar di database.")

df_kategori = pd.DataFrame()
if len(data_user_bulan_ini) > 0:
    df = pd.DataFrame(data_user_bulan_ini, columns=["Tanggal", "Keterangan", "Kategori", "Nominal", "Username"])
    df['Nominal'] = df['Nominal'].astype(str).str.replace(r'[^\d]', '', regex=True)
    df['Nominal'] = pd.to_numeric(df['Nominal'], errors='coerce').fillna(0)
    df_kat = df.groupby('Kategori')['Nominal'].sum().reset_index()
    df_kategori = df_kat.set_index('Kategori')

# ==================================
# HEADER & DASHBOARD DINAMIS
# ==================================
st.markdown('<div class="hero"><h1>🧾 ScanStruk AI V5</h1><p style="font-size:18px;">Advanced Financial Assistant • Income Tracking & Verification System</p></div>', unsafe_allow_html=True)

# Kalkulasi Sisa Jatah Anggaran Baru (Batas Anggaran + Total Masuk - Total Keluar)
sisa_anggaran = (target_anggaran + total_bulan_ini_masuk) - total_bulan_ini_keluar
total_dompet_aktif = target_anggaran + total_bulan_ini_masuk

if total_dompet_aktif > 0:
    persentase_dompet = min(total_bulan_ini_keluar / total_dompet_aktif, 1.0)
else:
    persentase_dompet = 0.0

st.markdown(
    f"""
    <div class="target-card">
        <h4 style="color: #0369a1 !important; margin-bottom: 5px;">📉 Sisa Jatah Anggaran {nama_pengguna} Bulan Ini:</h4>
        <h2>Rp {int(sisa_anggaran):,}</h2>
        <p style="color: #0c4a6e !important; font-size: 14px; margin-top: 10px;">
            (Batas Bulanan Rp {int(target_anggaran):,} + Total Pemasukan Rp {int(total_bulan_ini_masuk):,} - Total Pengeluaran Rp {int(total_bulan_ini_keluar):,})
        </p>
    </div>
    """, unsafe_allow_html=True
)
st.progress(persentase_dompet, text=f"Dana Terpakai: {int(persentase_dompet * 100)}% dari Total Kapasitas Dompet")
st.markdown("<br>", unsafe_allow_html=True)

# Tampilan 3 Kotak Metrik Sejajar (INOVASI 2)
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.markdown(f'<div class="metric-today"><h4>💸 Keluar Hari Ini</h4><h2>Rp {int(total_hari_ini_keluar):,}</h2></div>', unsafe_allow_html=True)
with col_m2:
    st.markdown(f'<div class="metric-month"><h4>📉 Keluar Bulan Ini</h4><h2>Rp {int(total_bulan_ini_keluar):,}</h2></div>', unsafe_allow_html=True)
with col_m3:
    st.markdown(f'<div class="metric-income"><h4>💰 Masuk Bulan Ini</h4><h2>Rp {int(total_bulan_ini_masuk):,}</h2></div>', unsafe_allow_html=True)

# Tampilan Grafik
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div class='card' style='text-align: center;'><b>📊 Grafik Distribusi Alokasi Dana Pengeluaran Bulan Ini</b>", unsafe_allow_html=True)
if not df_kategori.empty:
    st.bar_chart(df_kategori, height=200)
else:
    st.info("Belum ada transaksi pengeluaran di bulan ini.")
st.markdown("</div>", unsafe_allow_html=True)

# ==================================
# AREA INPUT DATA (HYBRID)
# ==================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f'<div class="card"><h3>📥 Tambah Catatan Finansial ({nama_pengguna})</h3></div>', unsafe_allow_html=True)

tab_manual, tab_ai = st.tabs(["📝 Catat Manual", "📷 Pindai Struk / Bukti Transfer (Otomatis)"])

with tab_manual:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("form_pencatatan_manual", clear_on_submit=True):
        col_form1, col_form2 = st.columns(2)
        with col_form1:
            tgl_manual = st.date_input("Tanggal Transaksi", value=datetime.utcnow() + timedelta(hours=7))
            ket_manual = st.text_input("Keterangan Pengeluaran/Pemasukan", placeholder="Contoh: Gaji Bulanan, Beli Sepatu, Bayar Kos")
        with col_form2:
            kat_manual = st.selectbox("Pilih Kategori", daftar_kategori)
            nom_manual = st.number_input("Nominal Uang (Rp)", min_value=0, step=500, value=0)
            
        btn_simpan_manual = st.form_submit_button("💾 Simpan Catatan")
        
        if btn_simpan_manual:
            if ket_manual.strip() != "" and nom_manual > 0:
                format_tgl = tgl_manual.strftime("%Y-%m-%d")
                sheet_riwayat.append_row([format_tgl, ket_manual.strip(), kat_manual, int(nom_manual), nama_pengguna])
                st.success(f"✅ Berhasil mencatat: {ket_manual}!")
                st.rerun()
            else:
                st.warning("⚠️ Isian tidak lengkap.")

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
            
            if st.button("🔍 Jalankan Pemindaian AI"):
                with st.spinner("🤖 AI sedang membaca data..."):
                    proses_image = Image.open(image_file)
                    proses_image.thumbnail((1000, 1000))
                    
                    prompt = f"""
                    Anda adalah asisten keuangan pribadi teliti. Baca struk atau screenshot transaksi ini.
                    Ekstrak informasi berikut dengan akurat:
                    1. "tanggal": Ambil tanggal di gambar (format YYYY-MM-DD). Jika tidak ada atau sudah lewat bulan, WAJIB gunakan tanggal hari ini: {waktu_hari_ini}.
                    2. "keterangan": Nama toko atau rincian singkat.
                    3. "kategori": Pilih SATU yang paling cocok: [Makanan & Minuman, Transportasi, Kebutuhan Kuliah/Kos, Tagihan & Pulsa/Internet, Hiburan & Game, Tabungan & Investasi, Lainnya].
                    4. "nominal": Total akhir uang. Angka murni tanpa titik/Rp.

                    Balas HANYA format JSON seperti ini:
                    {{"tanggal": "{waktu_hari_ini}", "keterangan": "Beli Sesuatu", "kategori": "Lainnya", "nominal": 20000}}
                    """
                    
                    try:
                        response = client.models.generate_content(model="gemini-2.5-flash", contents=[prompt, proses_image], config=types.GenerateContentConfig(temperature=0.0))
                        
                        teks_kotor = response.text
                        teks_bersih = teks_kotor.replace("```json", "")
                        result_text = teks_bersih.replace("```", "").strip()
                        
                        # INOVASI 1: Jangan langsung simpan ke Sheets, masukkan dulu ke Session State untuk di-review
                        st.session_state.ai_preview_data = json.loads(result_text)
                        st.success("🤖 AI Selesai Membaca! Silakan periksa hasilnya di bawah.")
                    except Exception as e:
                        st.error(f"Gagal memproses gambar: {e}")
        else:
            st.info("Sediakan gambar struk terlebih dahulu.")

    # INOVASI 1: AREA KONFIRMASI DAN EDIT HASIL SCAN AI BEFORE SAVE
    if st.session_state.ai_preview_data:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="preview-box"><h3>🔍 Kotak Koreksi Hasil Scan AI</h3><p>AI bisa saja salah membaca tanggal lama atau nominal. Silakan ubah angka di bawah ini sebelum disimpan secara resmi ke database!</p></div>', unsafe_allow_html=True)
        
        with st.form("form_konfirmasi_ai"):
            p_data = st.session_state.ai_preview_data
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                # Mengubah teks string tanggal dari AI menjadi objek tanggal Streamlit agar bisa diedit lewat kalender
                try: tgl_obj = datetime.strptime(p_data.get("tanggal", waktu_hari_ini), "%Y-%m-%d")
                except: tgl_obj = datetime.strptime(waktu_hari_ini, "%Y-%m-%d")
                
                v_tanggal = st.date_input("Koreksi Tanggal", value=tgl_obj)
                v_keterangan = st.text_input("Koreksi Nama Toko/Keterangan", value=p_data.get("keterangan", ""))
            with col_v2:
                # Menentukan index pilihan kategori bawaan dari AI
                ai_kat = p_data.get("kategori", "Lainnya")
                def_idx = daftar_kategori.index(ai_kat) if ai_kat in daftar_kategori else 7
                
                v_kategori = st.selectbox("Koreksi Kategori", daftar_kategori, index=def_idx)
                v_nominal = st.number_input("Koreksi Total Nominal (Rp)", value=int(p_data.get("nominal", 0)), min_value=0)
            
            btn_fix_save = st.form_submit_button("✅ DATA SUDAH BENAR - SIMPAN KE SHEET")
            
            if btn_fix_save:
                sheet_riwayat.append_row([v_tanggal.strftime("%Y-%m-%d"), v_keterangan.strip(), v_kategori, int(v_nominal), nama_pengguna])
                st.session_state.ai_preview_data = None # Reset kotak preview setelah sukses
                st.success("✅ Data hasil koreksi sukses disimpan ke Google Sheets!")
                st.rerun()

# ==================================
# TABEL HISTORI, UNDO, & DOWNLOAD REPORT (INOVASI 3)
# ==================================
if len(data_user_semua) > 0:
    st.markdown("---")
    
    col_h1, col_h2, col_h3 = st.columns([2.5, 1, 1])
    with col_h1:
        st.markdown(f"### 📋 Daftar Transaksi Pengguna ({nama_pengguna})")
    
    # INOVASI 3: MEMBUAT TOMBOL DOWNLOAD CSV LAPORAN BULANAN
    with col_h2:
        if len(data_user_semua) > 0:
            df_export = pd.DataFrame(data_user_semua, columns=["Tanggal", "Keterangan", "Kategori", "Nominal", "Username"])
            csv_data = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Unduh File Excel/CSV",
                data=csv_data,
                file_name=f"Laporan_Keuangan_{nama_pengguna}.csv",
                mime="text/csv"
            )
            
    with col_h3:
        if baris_terakhir_user:
            if st.button("🗑️ Undo Transaksi Terakhir", type="primary"):
                try:
                    sheet_riwayat.delete_rows(baris_terakhir_user)
                    st.success("Berhasil dihapus!")
                    st.rerun()
                except:
                    st.error("Gagal menghapus.")

    data_terbalik = data_user_semua[::-1][:10] 
    for item in data_terbalik:
        try:
            nom_bersih = str(item[3]).replace("Rp", "").replace(".", "").replace(",", "").strip()
            nominal_rupiah = f"Rp {int(nom_bersih):,}"
        except: 
            nominal_rupiah = item[3]
        
        icon = "💰" if item[2] == "Pemasukan (Gaji/Uang Saku)" else "📉"
        st.markdown(f"{icon} **{item[0]}** | {item[1]} — **{nominal_rupiah}** *({item[2]})*")
