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

# Custom CSS untuk mempercantik UI, Font, dan Tombol
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1 { font-weight: 800; color: #1E293B; letter-spacing: -0.05em; }
    h2, h3 { font-weight: 700; color: #334155; margin-top: 1.5rem; }
    .stButton>button {
        background-color: #2563EB; color: white; border-radius: 8px;
        font-weight: 600; padding: 0.6rem 2rem; border: none;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover { background-color: #1D4ED8; transform: translateY(-1px); }
    [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; color: #1E3A8A; }
    .footer { text-align: center; margin-top: 3rem; color: #94A3B8; font-size: 0.85rem; }
    </style>
""", unsafe_allow_html=True)

# HEADER UTAMA
st.title("🏢 SPEEDHOME Property Price Intelligence")
st.caption("Aplikasi otomatis analisis data harga sewa properti SPEEDHOME Malaysia (Local Data Storage Mode)")

# DROPDOWN PILIHAN AREA
area_options = ["Kuala Lumpur", "Cyberjaya", "Mont Kiara"]
selected_area = st.selectbox("Pilih atau ketik nama area/apartemen:", options=area_options)

# Menentukan file JSON berdasarkan dropdown
search_keyword = selected_area.lower().replace(" ", "_")
json_filename = f"{search_keyword}.json"

st.markdown("---")

# Cek keberadaan file data lokal
if os.path.exists(json_filename):
    try:
        with open(json_filename, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        properties = json_data.get('pageProps', {}).get('propertyList', {}).get('content', [])
        
        if properties:
            raw_df = pd.DataFrame(properties)
            
            # Pemetaan Data Mandatori
            df = pd.DataFrame()
            df['Judul Listing'] = raw_df['name'] if 'name' in raw_df else "Unit " + raw_df.index.astype(str)
            df['Area'] = selected_area
            
            if 'bedroom' in raw_df:
                df['Tipe'] = raw_df['bedroom'].apply(lambda x: f"{int(x)}BR" if pd.notnull(x) and x > 0 else "Studio")
            else:
                df['Tipe'] = "Studio"
                
            df['Bulanan (RM)'] = raw_df['price'].astype(float) if 'price' in raw_df else 1500.0
            df['Tahunan (RM)'] = df['Bulanan (RM)'] * 12
            df['Sqft'] = raw_df['sqft'].astype(float) if 'sqft' in raw_df else 850.0
            df['Furnish'] = raw_df['furnishType'].fillna("PARTIAL")
            
            if 'ref' in raw_df:
                df['Link'] = raw_df['ref'].apply(lambda x: f"https://speedhome.com/ads/{x}")
            else:
                df['Link'] = "https://speedhome.com"
            
            # --- PROSES STATISTIK RINGKASAN ---
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
            
            # ==========================================
            # DASHBOARD LAYOUT
            # ==========================================
            
            # BARIS 1: METRICS CARDS
            st.markdown("### 📌 Sekilas Pasar Properti")
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric(label="Total Unit Terdaftar", value=f"{len(df)} Unit")
            with m2:
                st.metric(label="Rata-rata Harga Sewa", value=f"RM {round(df['Bulanan (RM)'].mean(), 2)}")
            with m3:
                st.metric(label="Median Sewa", value=f"RM {df['Bulanan (RM)'].median()}")
            with m4:
                st.metric(label="Rata-rata Ukuran", value=f"{round(df['Sqft'].mean(), 1)} Sqft")
            
            st.markdown("---")
            
            # BARIS 2: VISUALISASI GRAFIK
            st.markdown("### 📊 Tren & Distribusi Market")
            g1, g2 = st.columns([3, 2])
            
            with g1:
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(x=summary_df["Tipe Unit"], y=summary_df["Avg (RM)"], name="Rata-rata (Avg)", marker_color='#2563EB'))
                fig_bar.add_trace(go.Bar(x=summary_df["Tipe Unit"], y=summary_df["Median"], name="Median / Fair Price", marker_color='#10B981'))
                
                fig_bar.update_layout(
                    title="Perbandingan Harga Sewa Berdasarkan Tipe Unit (RM)",
                    barmode='group',
                    hovermode="x unified",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with g2:
                furnish_counts = df['Furnish'].value_counts().reset_index()
                furnish_counts.columns = ['Status', 'Jumlah']
                fig_pie = px.pie(
                    furnish_counts, names='Status', values='Jumlah',
                    title="Komposisi Furnishing Unit",
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_pie.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_pie, use_container_width=True)
                
            st.markdown("---")
            
            # BARIS 3: TABEL STATISTIK & EXCEL DOWNLOAD
            st.markdown("### 📊 Tabel Ringkasan Harga (Price Summary)")
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # Fitur Unduh Excel dalam expander
            with st.expander("📥 Ambil File Laporan Analisis Market"):
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Daftar Unit', index=False)
                    summary_df.to_excel(writer, sheet_name='Ringkasan Statistik', index=False)
                
                date_str = datetime.now().strftime("%Y%m%d")
                st.download_button(
                    label="🟢 Download Dokumen Riset Pasar (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"SPEEDHOME_Report_{search_keyword}_{date_str}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
            st.markdown("---")
            
            # BARIS 4: DETAIL LISTING
            st.markdown("### 🔍 Detail Semua Unit Properti")
            st.dataframe(
                df.style.format({"Bulanan (RM)": "RM {:.2f}", "Tahunan (RM)": "RM {:.2f}", "Sqft": "{:.0f} sqft"}),
                use_container_width=True,
                hide_index=True
            )
            
        else:
            st.warning("⚠️ Struktur file data ditemukan, tetapi kontennnya kosong.")
            
    except Exception as e:
        st.error(f"❌ Gagal memproses visualisasi internal: {str(e)}")
else:
    st.info(f"💡 File database `{json_filename}` belum terdeteksi di repositori Anda. Harap pastikan nama file JSON yang Anda simpan di GitHub menggunakan format huruf kecil semua dan underscore (contoh: `kuala_lumpur.json`, `cyberjaya.json`, atau `mont_kiara.json`).")

st.markdown('<div class="footer">SPEEDHOME Price Intelligence App Engine v2.0 • Created with ❤️</div>', unsafe_style_allowed=True)
