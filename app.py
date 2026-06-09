import streamlit as st
import cloudscraper  # Menggunakan cloudscraper untuk bypass Cloudflare
import pandas as pd
from datetime import datetime
import io

# Setup halaman agar responsif & lebar
st.set_page_config(page_title="SPEEDHOME Price Intelligence", layout="wide")

st.title("🏢 SPEEDHOME Property Price Intelligence")
st.caption("Aplikasi otomatis pengumpul dan analisis data harga sewa properti SPEEDHOME Malaysia")

# 1. KOLOM INPUT & DROPDOWN SIMULASI (Requirement 1)
area_options = ["Mont Kiara", "Bangsar", "Cyberjaya", "Kuala Lumpur"]
selected_area = st.selectbox("Pilih atau ketik nama area/apartemen:", options=area_options)

# Tombol untuk memicu scraping
if st.button("🚀 Ambil Data Otomatis", use_container_width=True):
    
    # Normalisasi string untuk URL (contoh: "Mont Kiara" -> "mont")
    search_keyword = selected_area.split()[0].lower()
    
    with st.spinner(f"Sedang mengambil data publik SPEEDHOME untuk area: {selected_area}..."):
        try:
            # URL endpoint data Next.js
            build_id = "1780918065278"  
            url = f"https://speedhome.com/_next/data/build-{build_id}/en/rent/{search_keyword}.json"
            
            params = {"q": selected_area, "category": "LOCATION", "loc": search_keyword}
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
                "Referer": f"https://speedhome.com/rent/{search_keyword}",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "X-Requested-With": "XMLHttpRequest"
            }
            
            # --- PROSES BYPASS MENGGUNAKAN CLOUDSCRAPER ---
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                json_data = response.json()
                properties = json_data.get('pageProps', {}).get('properties', [])
                
                if properties:
                    raw_df = pd.DataFrame(properties)
                    
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
                    st.write("Tabel di bawah ini dapat di-scroll secara horizontal dan responsif di layar HP.")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                else:
                    st.warning("Data properti kosong atau tidak ditemukan untuk area ini.")
            else:
                st.error(f"Gagal mengambil data dari SPEEDHOME. (Status Code: {response.status_code})")
        except Exception as e:
            st.error(f"Terjadi kendala koneksi: {str(e)}")
