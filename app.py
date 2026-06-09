import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import json
import os

# 1. KONFIGURASI HALAMAN PREMIUM
st.set_page_config(
    page_title="SPEEDHOME Insights",
    page_icon="🏢",
    layout="wide"
)

# Custom CSS untuk mempercantik UI
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1 { font-weight: 800; color: #1E293B; letter-spacing: -0.05em; }
    h2, h3 { font-weight: 700; color: #334155; margin-top: 1.5rem; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; color: #1E3A8A; }
    .footer { text-align: center; margin-top: 3rem; color: #94A3B8; font-size: 0.85rem; }
    </style>
""", unsafe_allow_html=True)

# HEADER UTAMA
st.title("🏢 SPEEDHOME Property Price Intelligence")
st.caption("Aplikasi otomatis analisis data sewa properti - Smart Auto-Extract Mode")
st.markdown("---")

# 2. LOAD DATABASE INDUK (Contoh: kuala_lumpur.json)
# File ini bertindak sebagai pusat data yang berisi gabungan banyak apartemen
MASTER_FILE = "kuala_lumpur.json"

if os.path.exists(MASTER_FILE):
    try:
        with open(MASTER_FILE, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        raw_properties = json_data.get('pageProps', {}).get('propertyList', {}).get('content', [])
        
        if raw_properties:
            # Bangun Dataframe Induk Terlebih Dahulu
            main_raw_df = pd.DataFrame(raw_properties)
            
            # Bersihkan dan petakan kolom mendasar
            master_df = pd.DataFrame()
            master_df['Judul Listing'] = main_raw_df['name'] if 'name' in main_raw_df else "Unit Properti"
            
            # Mengambil ekstrak nama Kondominium/Apartemen dari judul properti
            # Biasanya SPEEDHOME menulis nama properti di awal judul, kita jadikan referensi filter
            master_df['Nama Apartemen'] = master_df['Judul Listing'].apply(lambda x: str(x).split(",")[0].strip())
            
            if 'bedroom' in main_raw_df:
                master_df['Tipe'] = main_raw_df['bedroom'].apply(lambda x: f"{int(x)}BR" if pd.notnull(x) and x > 0 else "Studio")
            else:
                master_df['Tipe'] = "Studio"
                
            master_df['Bulanan (RM)'] = main_raw_df['price'].astype(float) if 'price' in main_raw_df else 1500.0
            master_df['Tahunan (RM)'] = master_df['Bulanan (RM)'] * 12
            master_df['Sqft'] = main_raw_df['sqft'].astype(float) if 'sqft' in main_raw_df else 850.0
            master_df['Furnish'] = main_raw_df['furnishType'].fillna("PARTIAL")
            master_df['Link'] = main_raw_df['ref'].apply(lambda x: f"https://speedhome.com/ads/{x}") if 'ref' in main_raw_df else "https://speedhome.com"

            # --- AMBIL DAFTAR APARTEMEN SECARA OTOMATIS (AUTO-EXTRACT) ---
            # Semua nama apartemen unik di dalam JSON akan dikumpulkan di sini secara otomatis
            list_apartemen_unik = sorted(master_df['Nama Apartemen'].unique().tolist())
            
            # 3. FITUR PENCARIAN OTOMATIS BERDASARKAN HASIL EXTRACT
            selected_apartment = st.selectbox(
                "🔍 Ketik nama apartemen atau pilih dari daftar database otomatis:",
                options=list_apartemen_unik,
                index=None,
                placeholder="Ketik untuk mencari apartemen (Contoh: Arte, The Elements, Saffron...)"
            )
            
            st.markdown("---")
            
            # 4. LOGIKA FILTER BERDASARKAN PILIHAN USER
            if selected_apartment:
                # Saring data master hanya untuk apartemen yang dipilih
                df = master_df[master_df['Nama Apartemen'] == selected_apartment].reset_index(drop=True)
                
                # JALANKAN ANALISIS STATISTIK SECARA LIVE
                summary_data = []
                for tipe, group in df.groupby('Tipe'):
                    summary_data.append({
                        "Tipe Unit": tipe,
                        "Jumlah Unit": len(group),
                        "Avg (RM)": round(group['Bulanan (RM)'].mean(), 2),
                        "Median": group['Bulanan (RM)'].median(),
                        "Modus": group['Bulanan (RM)'].mode().iloc[0] if not group['Bulanan (RM)'].mode().empty else group['Bulanan (RM)'].median(),
                        "Fair Price": group['Bulanan (RM)'].median(),
                        "Avg Sqft": round(group['Sqft'].mean(), 2)
                    })
                summary_df = pd.DataFrame(summary_data)
                
                # --- DISPLAY DASHBOARD PREMIUM ---
                st.markdown(f"### 📊 Hasil Intelijen Pasar: {selected_apartment}")
                
                # BARIS 1: METRICS CARDS LIVE
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric(label="Total Unit Ditemukan", value=f"{len(df)} Unit")
                with m2:
                    st.metric(label="Rata-rata Sewa", value=f"RM {round(df['Bulanan (RM)'].mean(), 2)}")
                with m3:
                    st.metric(label="Median Sewa", value=f"RM {df['Bulanan (RM)'].median()}")
                with m4:
                    st.metric(label="Rata-rata Ukuran", value=f"{round(df['Sqft'].mean(), 1)} Sqft")
                
                st.markdown("---")
                
                # BARIS 2: VISUALISASI GRAFIK PLOTLY
                st.markdown("### 📈 Tren & Distribusi Properti")
                g1, g2 = st.columns([3, 2])
                
                with g1:
                    fig_bar = go.Figure()
                    fig_bar.add_trace(go.Bar(x=summary_df["Tipe Unit"], y=summary_df["Avg (RM)"], name="Rata-rata (Avg)", marker_color='#2563EB'))
                    fig_bar.add_trace(go.Bar(x=summary_df["Tipe Unit"], y=summary_df["Median"], name="Median / Fair Price", marker_color='#10B981'))
                    fig_bar.update_layout(
                        title="Perbandingan Harga Sewa (RM)", barmode='group',
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                with g2:
                    furnish_counts = df['Furnish'].value_counts().reset_index()
                    furnish_counts.columns = ['Status', 'Jumlah']
                    fig_pie = px.pie(furnish_counts, names='Status', values='Jumlah', title="Komposisi Furnishing")
                    fig_pie.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                st.markdown("---")
                
                # BARIS 3: TABEL STATISTIK & DOWNLOAD BUTTON
                st.markdown("### 📋 Tabel Ringkasan Harga (Price Summary)")
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                with st.expander("📥 Download Laporan Analisis (.xlsx)"):
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Daftar Unit', index=False)
                        summary_df.to_excel(writer, sheet_name='Ringkasan', index=False)
                    st.download_button(
                        label="🟢 Unduh Dokumen Excel", data=buffer.getvalue(),
                        file_name=f"SPEEDHOME_Report_{selected_apartment.lower().replace(' ', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                st.markdown("---")
                
                # BARIS 4: DETAIL ALL LISTINGS
                st.markdown("### 🔍 Detail Semua Unit Properti")
                st.dataframe(
                    df.style.format({"Bulanan (RM)": "RM {:.2f}", "Tahunan (RM)": "RM {:.2f}", "Sqft": "{:.0f} sqft"}),
                    use_container_width=True, hide_index=True
                )
            else:
                st.info("👋 Database siap! Silakan pilih atau ketik nama apartemen pada kolom di atas untuk mulai melakukan analisa otomatis.")
                
        else:
            st.warning("⚠️ File data induk ditemukan, tetapi data listing properti di dalamnya kosong.")
            
    except Exception as e:
        st.error(f"❌ Gagal memproses data induk: {str(e)}")
else:
    st.error(f"❌ File database utama `{MASTER_FILE}` tidak ditemukan di repositori GitHub Anda. Silakan upload file data master area Anda terlebih dahulu.")

st.markdown('<div class="footer">SPEEDHOME Price Intelligence App Engine v3.0 • Automated Mode</div>', unsafe_allow_html=True)
