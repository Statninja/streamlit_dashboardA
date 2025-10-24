# app.py
# PanditaData Disaster & Space Intelligence Platform
# Works on Streamlit Cloud with ONLY a .py URL
# -------------------------------------------------
import streamlit as st
import sys
import importlib.util

# -------------------------------------------------
# 1. PACKAGE CHECKER – tells you exactly what to add
# -------------------------------------------------
REQUIRED = {
    "requests": "requests>=2.31.0",
    "pandas": "pandas>=2.0.0",
    "numpy": "numpy>=1.24.0",
    "geopy": "geopy>=2.3.0",
    "plotly": "plotly>=5.18.0",
    "astropy": "astropy>=6.0.0",
    "reportlab": "reportlab>=4.0.0",
}

missing = []
for mod, req in REQUIRED.items():
    if importlib.util.find_spec(mod) is None:
        missing.append(req)

if missing:
    st.error("Missing packages – add them to **requirements.txt** in your repo:")
    for r in missing:
        st.code(r)
    st.info(
        "How to add:\n"
        "1. Open your repo on GitHub\n"
        "2. Click **Add file → Create new file**\n"
        "3. Name it `requirements.txt`\n"
        "4. Paste the lines above\n"
        "5. Commit → Streamlit will rebuild automatically"
    )
    st.stop()   # stop execution until packages are installed

# -------------------------------------------------
# 2. ALL IMPORTS (now guaranteed to exist)
# -------------------------------------------------
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import base64
from io import BytesIO

# -------------------------------------------------
# 3. PAGE CONFIG & CSS
# -------------------------------------------------
st.set_page_config(page_title="PanditaData", page_icon="Globe", layout="wide")
st.markdown(
    """
    <style>
    .main{background:#0e1117;color:#fafafa;}
    .critical-alert{background:#8b0000;color:#fff;padding:15px;border-radius:8px;
                    border-left:5px solid #ff0000;margin:8px 0;font-weight:bold;}
    .high-alert{background:#ff8c00;color:#fff;padding:12px;border-radius:8px;
                border-left:5px solid #ffa500;margin:8px 0;}
    .moderate-alert{background:#ffd700;color:#000;padding:12px;border-radius:8px;
                    border-left:5px solid #ffff00;margin:8px 0;}
    h1{color:#4da6ff;} h2{color:#66b3ff;border-bottom:2px solid #4da6ff;padding-bottom:8px;}
    .footer{position:fixed;bottom:0;left:0;width:100%;background:#1a1a1a;color:#888;
            text-align:center;padding:8px;font-size:12px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# 4. AUTH & SAVED LOCATIONS
# -------------------------------------------------
if "auth" not in st.session_state:
    st.session_state.update(
        {"auth": False, "saved": [], "lat": 37.7749, "lon": -122.4194}
    )

def login():
    if st.session_state.auth:
        return True
    with st.sidebar:
        st.subheader("Login (demo)")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("Login") and u == "user" and p == "pass":
            st.session_state.auth = True
            st.rerun()
    return False

if not login():
    st.stop()

# -------------------------------------------------
# 5. GEOCODING
# -------------------------------------------------
geo = Nominatim(user_agent="pandita_app")

def geocode(q):
    try:
        loc = geo.geocode(q, timeout=10)
        return loc and {"lat": loc.latitude, "lon": loc.longitude, "addr": loc.address}
    except:
        return None

def rev(lat, lon):
    try:
        return geo.reverse(f"{lat},{lon}", timeout=10).address
    except:
        return "Unknown"

# -------------------------------------------------
# 6. EARTHQUAKE + AFTERSHOCK
# -------------------------------------------------
USGS = "https://earthquake.usgs.gov/fdsnws/event/1/query"

def fetch_eq(lat, lon, r, s, e, m):
    p = {
        "format": "geojson",
        "starttime": s,
        "endtime": e,
        "latitude": lat,
        "longitude": lon,
        "maxradiuskm": r,
        "minmagnitude": m,
        "limit": 20000,
        "eventtype": "earthquake",
    }
    try:
        return requests.get(USGS, params=p, timeout=30).json()
    except:
        return None

def process_eq(data, ulat, ulon):
    if not data or "features" not in data:
        return pd.DataFrame()
    rows = []
    for f in data["features"]:
        p = f["properties"]
        c = f["geometry"]["coordinates"]
        dist = geodesic((ulat, ulon), (c[1], c[0])).km
        rows.append(
            {
                "time": datetime.fromtimestamp(p["time"] / 1000),
                "mag": p["mag"],
                "depth": c[2],
                "dist": round(dist, 1),
                "place": p["place"],
            }
        )
    return pd.DataFrame(rows).sort_values("time", ascending=False)

def aftershock(mag, days):
    K = 10 ** (mag - 4.5)
    rate = K / (0.05 + days) ** 1.1
    prob = 1 - np.exp(-rate * 7 * 0.05)
    rec = "HIGH" if prob > 0.5 else "MODERATE" if prob > 0.2 else "LOW"
    return {"rate": round(rate, 2), "prob": round(prob * 100, 1), "rec": rec}

# -------------------------------------------------
# 7. WEATHER + NWS ALERTS
# -------------------------------------------------
OM = "https://api.open-meteo.com/v1/forecast"
NWS = "https://api.weather.gov/alerts"

def fetch_weather(lat, lon):
    p = {"latitude": lat, "longitude": lon, "current_weather": "true"}
    try:
        return requests.get(OM, params=p, timeout=30).json()
    except:
        return None

def fetch_alerts(lat, lon):
    try:
        r = requests.get(
            f"{NWS}/active?point={lat},{lon}",
            headers={"User-Agent": "PanditaData/1.0", "Accept": "application/geo+json"},
            timeout=30,
        ).json()
        return [f["properties"] for f in r.get("features", [])]
    except:
        return []

# -------------------------------------------------
# 8. SPACE WEATHER & HURRICANES
# -------------------------------------------------
def fetch_space():
    try:
        kp = requests.get(
            "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json", timeout=10
        ).json()[-1]["kp_index"]
        return {"kp": kp}
    except:
        return {"kp": 0}

def fetch_hurricanes():
    try:
        r = requests.get(
            "https://www.nhc.noaa.gov/CurrentStorms.json", timeout=10
        ).json()
        return [
            {"name": s["name"], "cat": s.get("classification", "TD")}
            for s in r.get("activeStorms", [])
        ]
    except:
        return []

# -------------------------------------------------
# 9. PDF EXPORT
# -------------------------------------------------
def make_pdf(lat, lon, eq, w, alerts, space):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter
    y = h - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "PanditaData Disaster Report")
    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Location: {rev(lat, lon)}")
    y -= 40
    if not eq.empty:
        c.drawString(50, y, "Recent Earthquakes:")
        y -= 20
        for _, r in eq.head(3).iterrows():
            c.drawString(70, y, f"{r['time']:%m-%d %H:%M} | M{r['mag']} | {r['dist']}km")
            y -= 18
    c.save()
    buf.seek(0)
    return buf.getvalue()

# -------------------------------------------------
# 10. SIDEBAR
# -------------------------------------------------
with st.sidebar:
    st.image("https://via.placeholder.com/200x60.png?text=PanditaData", width=200)
    sel = st.selectbox("Saved", [""] + [s["name"] for s in st.session_state.saved])
    if sel:
        for s in st.session_state.saved:
            if s["name"] == sel:
                st.session_state.lat, st.session_state.lon = s["lat"], s["lon"]
                st.rerun()
    name = st.text_input("Save current as:")
    if st.button("Save") and name:
        st.session_state.saved.append(
            {"name": name, "lat": st.session_state.lat, "lon": st.session_state.lon}
        )
        st.rerun()

    method = st.radio("Input", ["City", "Coords"])
    if method == "City":
        q = st.text_input("City/Address")
        if q:
            loc = geocode(q)
            if loc:
                st.session_state.lat, st.session_state.lon = loc["lat"], loc["lon"]
                st.success(loc["addr"])
    else:
        c1, c2 = st.columns(2)
        st.session_state.lat = c1.number_input(
            "Lat", value=st.session_state.lat, format="%.6f"
        )
        st.session_state.lon = c2.number_input(
            "Lon", value=st.session_state.lon, format="%.6f"
        )

    radius = st.slider("Radius (km)", 50, 1000, 300)
    days = st.slider("Days back", 1, 30, 7)
    min_mag = st.slider("Min Mag", 0.0, 6.0, 2.0, 0.1)

# -------------------------------------------------
# 11. MAIN DASHBOARD
# -------------------------------------------------
lat, lon = st.session_state.lat, st.session_state.lon
st.title(f"Report: {rev(lat, lon)}")

start = (datetime.now() - timedelta(days=ure=days)).strftime("%Y-%m-%d")
end = datetime.now().strftime("%Y-%m-%d")

# ----- Earthquakes -----
with st.spinner("Loading earthquakes..."):
    raw = fetch_eq(lat, lon, radius, start, end, min_mag)
    df = process_eq(raw, lat, lon) if raw else pd.DataFrame()

if not df.empty:
    st.subheader("Earthquake Activity")
    c1, c2, c3 = st.columns(3)
    c1.metric("Events", len(df))
    c2.metric("Max Mag", f"{df['mag'].max():.1f}")
    c3.metric("Closest", f"{df['dist'].min():.0f} km")

    # Aftershock
    main = df.iloc[0]
    days_since = (datetime.now() - main["time"]).days + 1
    ash = aftershock(main["mag"], days_since)
    st.info(
        f"**Aftershock Risk**: {ash['rec']} | {ash['prob']}% chance of M>{main['mag']-1:.1f} in 7 days"
    )

    fig = px.scatter_mapbox(
        df,
        lat="dist",
        lon="dist",
        color="mag",
        size="mag",
        hover_name="place",
        zoom=4,
        height=500,
        mapbox_style="open-street-map",
    )
    fig.add_trace(
        go.Scattermapbox(
            lat=[lat], lon=[lon], marker=dict(color="blue", size=15), name="You"
        )
    )
    st.plotly_chart(fig, use_container_width=True)

# ----- Weather -----
with st.spinner("Loading weather..."):
    w = fetch_weather(lat, lon)
if w:
    cw = w["current_weather"]
    st.subheader("Current Weather")
    c1, c2 = st.columns(2)
    c1.metric("Temp", f"{cw['temperature']:.1f}°C")
    c2.metric("Wind", f"{cw['windspeed']:.0f} km/h")

# ----- NWS Alerts -----
with st.spinner("Loading NWS alerts..."):
    alerts = fetch_alerts(lat, lon)
if alerts:
    st.subheader("NWS Severe Alerts")
    for a in alerts:
        sev = a["severity"]
        cls = (
            "critical-alert"
            if sev == "Extreme"
            else "high-alert"
            if sev == "Severe"
            else "moderate-alert"
        )
        st.markdown(
            f"<div class='{cls}'>{a['event']}: {a['headline']}</div>", unsafe_allow_html=True
        )

# ----- Space Weather -----
space = fetch_space()
st.subheader("Space Weather")
st.metric("Kp Index", f"{space['kp']:.1f}")

# ----- Hurricanes -----
hur = fetch_hurricanes()
if hur:
    st.subheader("Active Hurricanes")
    for h in hur:
        st.metric(h["name"], h["cat"])

# ----- PDF -----
if st.button("Download PDF Report"):
    pdf = make_pdf(lat, lon, df, w, alerts, space)
    b64 = base64.b64encode(pdf).decode()
    st.markdown(
        f'<a href="data:application/pdf;base64,{b64}" download="report.pdf">Download PDF</a>',
        unsafe_allow_html=True,
    )

st.markdown(
    "<div class='footer'>© 2025 PanditaData – Professional Disaster Intelligence</div>",
    unsafe_allow_html=True,
)
