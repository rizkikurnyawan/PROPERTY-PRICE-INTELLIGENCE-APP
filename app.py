import streamlit as st
import pandas as pd
from datetime import datetime
import io
import json
import os

# Setup halaman agar responsif & lebar
st.set_page_config(page_title="SPEEDHOME Price Intelligence", layout="wide")

st.title("🏢 SPEEDHOME Property Price Intelligence")
st.caption("Aplikasi otomatis analisis data harga sewa properti SPEEDHOME Malaysia (Local Data Storage Mode)")

# 1. KOLOM INPUT & DROPDOWN (Requirement 1)
area_options = ["Mont Kiara", "Cyberjaya"]
selected_area = st.selectbox("Pilih atau ketik nama area/apartemen:", options=area_options)

# Tombol untuk memicu pemrosesan data
if st.button("🚀 Ambil & Analisis Data", use_container_width=True):
    
    # Menentukan nama file berdasarkan drop-down (contoh: "Mont Kiara" -> "mont.json")
    search_keyword = selected_area.split()[0].lower()
    json_filename = f"{search_keyword}.json"
    
    with st.spinner(f"Sedang memproses database properti untuk area: {selected_area}..."):
        # Cek apakah file JSON hasil download manual kamu ada di GitHub
        if os.path.exists(json_filename):
            try:
                with open(json_filename, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Mengambil array data properti dari struktur bawaan Next.js
                properties = json_data.get('pageProps', {}).get('properties', [])
                
                if properties:
                    raw_df = pd.DataFrame(properties)
                    
                    # --- PEMETAAN DATA UNTUK MEMENUHI REQUIREMENT ---
                    df = pd.DataFrame()
                    df['Judul Listing'] = raw_df['title'] if 'title' in raw_df else "Unit " + raw_df.index.astype(str)
                    df['Area'] = selected_area
                    df['Tipe'] = raw_df['bedrooms'].apply(lambda x: f"{int(x)}BR" if pd.notnull(x) else "Studio")
                    df['Bulanan (RM)'] = raw_df['price'].astype(float) if 'price' in raw_df else 1500.0
                    df['Tahunan (RM)'] = df['Bulanan (RM)'] * 12
                    df['Sqft'] = raw_df['sqft'].astype(float) if 'sqft' in raw_df else 850.0
                    df['Furnish'] = raw_df['furnished'].fillna("Partially Furnished") if 'furnished' in raw_df else "Fully Furnished"
                    df['Link'] = raw_df['id'].apply(lambda x: f"https://speedhome.com/ads/{x}")
                    
                    # 2. TABEL RINGKASAN HARGA / PRICE SUMMARY (Requirement 2 & 4)
                    st.subheader("📊 Tabel Ringkasan Harga (Price Summary)")
                    
                    summary_data = []
                    for tipe, group in df.groupby('Tipe'):
                        summary_data.append({
                            "Tipe Unit": tipe,
                            "Jumlah Unit": len(group),
                            "Avg (RM)": round(group['Bulanan (RM)'].mean(), 2),
                            "Median": group['Bulanan (RM)'].median(),
                            "Modus": group['Bulanan (RM)'].mode().iloc[0] if not group['Bulanan (RM)'].mode().empty else "N/A",
                            "Fair Price": group['Bulanan (RM)'].median(),
                            "Avg Sqft": round(group['Sqft'].mean(), 2)
                        })
                    
                    summary_df = pd.DataFrame(summary_data)
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)
                    
                    # 3. FITUR DOWNLOAD DATA EXCEL (Requirement 5)
                    st.subheader("📥 Unduh Hasil Analisis")
                    
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Daftar Unit', index=False)
                        summary_df.to_excel(writer, sheet_name='Ringkasan Statistik', index=False)
                    
                    date_str = datetime.now().strftime("%Y%m%d")
                    file_name = f"SPEEDHOME_{selected_area.replace(' ', '_')}_{date_str}.xlsx"
                    
                    st.download_button(
                        label="🟢 Download Data dalam Format Excel (.xlsx)",
                        data=buffer.getvalue(),
                        file_name=file_name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    # 4. TABEL DAFTAR UNIT / UNIT LISTINGS (Requirement 3)
                    st.subheader("📋 Daftar Unit Lengkap")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                else:
                    st.warning("Struktur data properti di dalam file JSON tidak sesuai.")
            except Exception as e:
                st.error(f"Gagal membaca file data: {str(e)}")
        else:
            st.error(f"File database '{json_filename}' belum di-upload ke GitHub. Silakan download JSON dari browser dan upload ke GitHub kamu terlebih dahulu.")
