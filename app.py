from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import requests

app = FastAPI()

# Mount folder static agar index.html bisa diakses
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/api/scrape")
def scrape_data(area: str):
    # Sesuai Request URL yang kamu temukan
    url = f"https://speedhome.com/_next/data/build-1780918065278/en/rent/{area}.json"
    r = requests.get(url)
    data = r.json()
    
    # Logic pengolahan data (Mean, Median, dsb) di sini
    # Untuk contoh, kita lempar data mentah dulu
    return data['pageProps']['properties']