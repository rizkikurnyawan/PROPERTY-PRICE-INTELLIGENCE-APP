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
st.caption("Aplikasi otomatis analisis data sewa properti - Clean Search Mode")
st.markdown("---")

# 2. LOAD DATABASE INDUK
MASTER_FILE = "kuala_lumpur.json"

if os.path.exists(MASTER_FILE):
    try:
        with open(MASTER_FILE, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        raw_properties = json_data.get('pageProps', {}).get('propertyList', {}).get('content', [])
        
        if raw_properties:
            main_raw_df = pd.DataFrame(raw_properties)
            
            # Bersihkan dan petakan kolom mendasar
            master_df = pd.DataFrame()
            master_df['Judul Listing'] = main_raw_df['name'] if 'name' in main_raw_df else "Unit Properti"
            
            # LOGIKA PEMISAHAN (SPLIT) NAMA APARTEMEN & DAERAH
            def ekstrasi_lokasi(judul):
                parts = str(judul).split(",")
                apartemen = parts[0].strip() if len(parts) > 0 else ""
                daerah = parts[1].strip() if len(parts) > 1 else "Kuala Lumpur"
                return pd.Series([apartemen, daerah])
            
            master_df[['Nama Apartemen', 'Nama Daerah']] = master_df['Judul Listing'].apply(ekstrasi_lokasi)
            
            if 'bedroom' in main_raw_df:
                master_df['Tipe'] = main_raw_df['bedroom'].apply(lambda x: f"{int(x)}BR" if pd.notnull(x) and x > 0 else "Studio")
            else:
                master_df['Tipe'] = "Studio"
                
            master_df['Bulanan (RM)'] = main_raw_df['price'].astype(float) if 'price' in main_raw_df else 1500.0
            master_df['Tahunan (RM)'] = master_df['Bulanan (RM)'] * 12
            master_df['Sqft'] = main_raw_df['sqft'].astype(float) if 'sqft' in main_raw_df else 850.0
            master_df['Furnish'] = main_raw_df['furnishType'].fillna("PARTIAL")
            master_df['Link'] = main_raw_df['ref'].apply(lambda x: f"https://speedhome.com/ads/{x}") if 'ref' in main_raw_df else "https://speedhome.com"

            # --- BUAT DAFTAR SUGGESTION TERPISAH ---
            daerah_unik = master_df['Nama Daerah'].dropna().unique().tolist()
            apartemen_unik = master_df['Nama Apartemen'].dropna().unique().tolist()
            
            daerah_unik = sorted([d for d in daerah_unik if d])
            apartemen_unik = sorted([a for a in apartments_unik if a]) if 'apartments_unik' in locals() else sorted([a for a in  apartemen_unik if a])
            
            # Sekarang list opsi murni hanya berisi nama Daerah dan nama Apartemen saja
            opsi_pencarian = daerah_unik + apartemen_unik
            
            # 3. FITUR PENCARIAN OTOMATIS (KOSONG DI AWAL)
            selected_option = st.selectbox(
                "🔍 Ketik nama daerah atau nama apartemen untuk memfilter spesifik:",
                options=opsi_pencarian,
                index=None,  # Membuat kolom langsung kosong/clean di awal tanpa text terblok
                placeholder="Ketik di sini... (Contoh: Bangi, Cheras, Villa Tropika, The ERA)"
            )
            
            st.markdown("---")
            
            # 4. LOGIKA FILTER PINTAR
            # Jika kolom pencarian kosong, otomatis tampilkan SEMUA data (Kuala Lumpur Master Data)
            if selected_option is None:
                df = master_df.copy()
                judul_analisis = "Kuala Lumpur (Semua Wilayah)"
            elif selected_option in daerah_unik:
                df = master_df[master_df['Nama Daerah'] == selected_option].reset_index(drop=True)
                judul_analisis = f"Wilayah: {selected_option}"
            else:
                df = master_df[master_df['Nama Apartemen'] == selected_option].reset_index(drop=True)
                judul_analisis = f"Apartemen: {selected_option}"
                
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
            st.markdown(f"### 📊 Hasil Intelijen Pasar: {judul_analisis}")
            
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
                if 'Furnish' in df and not df['Furnish'].empty:
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
                    file_name=f"SPEEDHOME_Report_{judul_analisis.lower().replace(' ', '_')}.xlsx",
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
            st.warning("⚠️ File data induk ditemukan, tetapi data listing properti di dalamnya kosong.")
            
    except Exception as e:
        st.error(f"❌ Gagal memproses data lokasi: {str(e)}")
else:
    st.error(f"❌ File database utama `{MASTER_FILE}` tidak ditemukan di repositori GitHub Anda. Silakan upload file data master area Anda terlebih dahulu.")

st.markdown('<div class="footer">SPEEDHOME Price Intelligence App Engine v3.3 • Clean Search Mode</div>', unsafe_allow_html=True)
