# -*- coding: utf-8 -*-
"""app.py

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1IuHhJCPIGatLQtTFwvaXcijCKb0fLgiJ
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
import requests
import time

API_TOKEN = '6006a1a469ec4d9df77382f5a4b196c544a1430f'

latlng = "6.554,68.176,35.674,97.395"

def safe_request(url, retries=3, backoff=2):
    for attempt in range(retries):
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                return res
        except:
            pass
        time.sleep(backoff * (attempt + 1))
    return None

print("📡 Fetching station list...")
resp = safe_request(f"https://api.waqi.info/map/bounds?token={API_TOKEN}&latlng={latlng}")

stations = []
if resp:
    json_data = resp.json()
    if json_data.get("status") == "ok":
        stations = json_data.get("data", [])
    else:
        print(" API returned error:", json_data.get("data"))
        raise Exception("Invalid API Key or error response")
else:
    print(" Failed to fetch stations.")
    raise Exception("Request failed")

records = []
for i, st in enumerate(stations, start=1):
    sid = st.get("uid")
    station_name = st.get("station", {}).get("name")
    if not sid or not station_name:
        continue

    url = f"https://api.waqi.info/feed/@{sid}/?token={API_TOKEN}"
    res = safe_request(url)
    if res:
        js = res.json()
        if js.get("status") == "ok":
            iaqi = js["data"].get("iaqi", {})
            records.append({
                "Station": station_name,
                "Lat": st.get("lat"),
                "Lon": st.get("lon"),
                "AQI": js["data"].get("aqi"),
                "PM2.5": iaqi.get("pm25", {}).get("v"),
                "PM10": iaqi.get("pm10", {}).get("v"),
                "CO": iaqi.get("co", {}).get("v"),
                "NO2": iaqi.get("no2", {}).get("v"),
                "SO2": iaqi.get("so2", {}).get("v"),
                "O3": iaqi.get("o3", {}).get("v"),
            })
    time.sleep(1.2)

if not records:
    raise Exception("No data fetched. Exiting.")

df = pd.DataFrame(records)
df.replace("-", pd.NA, inplace=True)

for col in ["PM2.5", "PM10", "CO", "NO2", "SO2", "O3", "AQI", "Lat", "Lon"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["Temperature"] = 25

def ppb_to_ugm3(ppb, mw, temp):
    return (ppb * mw * 273) / (22.4 * (273 + temp))

df["CO"] = ppb_to_ugm3(df["CO"], 28.01, df["Temperature"])
df["NO2"] = ppb_to_ugm3(df["NO2"], 46.01, df["Temperature"])
df["SO2"] = ppb_to_ugm3(df["SO2"], 64.07, df["Temperature"])
df["O3"] = ppb_to_ugm3(df["O3"], 48.00, df["Temperature"])

df.dropna(subset=["PM2.5", "PM10", "CO", "NO2", "SO2", "O3", "AQI", "Lat", "Lon"], inplace=True)

df.to_csv("cleaned_india_waqi.csv", index=False)
print(" cleaned_india_waqi.csv saved in Colab files")

features = ["PM2.5", "PM10", "CO", "NO2", "SO2", "O3"]
X = df[features]
y = df["AQI"]

model = RandomForestRegressor()
model.fit(X, y)

joblib.dump(model, "random_forest_model.pkl")
print(" random_forest_model.pkl saved in Colab files")

from google.colab import files
files.download("cleaned_india_waqi.csv")
files.download("random_forest_model.pkl")