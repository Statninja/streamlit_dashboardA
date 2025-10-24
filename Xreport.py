"""
PANDITADATA DISASTER & SPACE INTELLIGENCE PLATFORM
Full Enterprise-Grade Disaster Monitoring System
"""

import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import base64
from io import BytesIO

# --- Required Imports (Safe Fall-back) ---
try:
    from geopy.geocoders import Nominatim
    from geopy.distance import geodesic
    GEOPY = True
except ImportError:
    GEOPY = False
    st.error("Please install geopy: pip install geopy")

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY = True
except ImportError:
    PLOTLY = False
    st.error("Please install plotly: pip install plotly")

try:
    from astropy.time import Time
    from astropy.coordinates import EarthLocation, AltAz, get_sun, get_body
    import astropy.units as u
    ASTROPY = True
except ImportError:
    ASTROPY = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB = True
except ImportError:
    REPORTLAB = False
    st.error("Please install reportlab: pip install reportlab")

# ============================================================================
# 0. PAGE CONFIG & CSS
# ============================================================================
st.set_page_config(
    page_title="PanditaData Disaster Intelligence",
    page_icon="Globe",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css():
    st.markdown("""
    <style>
    .main {background:#0e1117;color:#fafafa;}
    .critical-alert{background:#8b0000;color:#fff;padding:15px;border-radius:8px;border-left:5px solid #ff0000;margin:8px 0;font-weight:bold;}
    .high-alert{background:#ff8c00;color:#fff;padding:12px;border-radius:8px;border-left:5px solid #ffa500;margin:8px 0;}
    .moderate-alert{background:#ffd700;color:#000;padding:12px;border-radius:8px;border-left:5px solid #ffff00;margin:8px 0;}
    h1{color:#4da6ff;} h2{color:#66b3ff;border-bottom:2px solid #4da6ff;padding-bottom:8px;}
    .footer{position:fixed;bottom:0;left:0;width:100%;background:#1a1a1a;color:#888;text-align:center;padding:8px;font-size:12px;}
    </style>
    """, unsafe_allow_html=True)
load_css()

# ============================================================================
# 1. USER AUTH & SAVED LOCATIONS
# ============================================================================
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.saved = []
    st.session_state.lat = 37.7749
    st.session_state.lon = -122.4194

def login():
    if st.session_state.auth:
        return True
    with st.sidebar:
        st.subheader("Login")
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            if user == "user" and pwd == "pass":
                st.session_state.auth = True
                st.success("Logged in")
                st.rerun()
            else:
                st.error("Invalid")
    return False

def save_loc(name):
    if name:
        st.session_state.saved.append({"name": name, "lat": st.session_state.lat, "lon": st.session_state.lon})
        st.success(f"Saved {name}")
        st.rerun()

# ============================================================================
# 2. GEOCODING
# ============================================================================
if GEOPY:
    geo = Nominatim(user_agent="pandita")
    def geocode(q): 
        try: 
            loc = geo.geocode(q, timeout=10)
            if loc: return {"lat": loc.latitude, "lon": loc.longitude, "addr": loc.address}
        except: pass
        return None
    def rev_geocode(lat, lon):
        try: return geo.reverse(f"{lat},{lon}", timeout=10).address
        except: return "Unknown"
else:
    def geocode(q): return None
    def rev_geocode(lat, lon): return "Unknown"

# ============================================================================
# 3. EARTHQUAKE + AFTERSHOCK
# ============================================================================
USGS = "https://earthquake.usgs.gov/fdsnws/event/1/query"

def fetch_eq(lat, lon, r, s, e, mag):
    p = {"format":"geojson","starttime":s,"endtime":e,"latitude":lat,"longitude":lon,
         "maxradiuskm":r,"minmagnitude":mag,"limit":20000,"eventtype":"earthquake"}
    try: return requests.get(USGS, params=p, timeout=30).json()
    except: return None

def process_eq(data, ulat, ulon):
    if not data or "features" not in data: return pd.DataFrame()
    rows = []
    for f in data["features"]:
        p = f["properties"]
        c = f["geometry"]["coordinates"]
        dist = geodesic((ulat, ulon), (c[1], c[0])).km
        rows.append({
            "time": datetime.fromtimestamp(p["time"]/1000),
            "mag": p["mag"], "depth": c[2], "dist": round(dist,1),
            "place": p["place"], "risk": classify_risk(p["mag"], p.get("alert"))
        })
    df = pd.DataFrame(rows).sort_values("time", ascending=False)
    return df

def classify_risk(mag, alert):
    if mag >= 8.0: return "CATASTROPHIC"
    if mag >= 7.0 or alert == "red": return "CRITICAL"
    if mag >= 6.0 or alert == "orange": return "SEVERE"
    if mag >= 5.0: return "MODERATE"
    if mag >= 4.0: return "MINOR"
    return "NEGLIGIBLE"

def aftershock(mag, days):
    K = 10 ** (mag - 4.5); c = 0.05; p = 1.1
    rate = K / (c + days) ** p
    prob = 1 - np.exp(-rate * 7 * 0.05)
    rec = "HIGH RISK" if prob > 0.5 else "MODERATE RISK" if prob > 0.2 else "LOW RISK"
    return {"rate": round(rate,2), "prob": round(prob*100,1), "rec": rec}

# ============================================================================
# 4. WEATHER + NWS ALERTS
# ============================================================================
OM = "https://api.open-meteo.com/v1/forecast"
NWS = "https://api.weather.gov/alerts"

def fetch_weather(lat, lon):
    p = {"latitude":lat,"longitude":lon,"current_weather":"true","timezone":"auto"}
    try: return requests.get(OM, params=p, timeout=30).json()
    except: return None

def fetch_alerts(lat, lon):
    url = f"{NWS}/active?point={lat},{lon}"
    h = {"User-Agent": "PanditaData/1.0", "Accept": "application/geo+json"}
    try:
        r = requests.get(url, headers=h, timeout=30).json()
        return [f["properties"] for f in r.get("features",[])]
    except: return []

# ============================================================================
# 5. SPACE WEATHER
# ============================================================================
def fetch_space():
    try:
        kp = requests.get("https://services.swpc.noaa.gov/json/planetary_k_index_1m.json", timeout=10).json()[-1]
        sw = requests.get("https://services.swpc.noaa.gov/json/rtsw/rtsw_wind_1m.json", timeout=10).json()[-1]
        return {
            "kp": kp.get("kp_index",0),
            "speed": sw.get("proton_speed",0),
            "flares": len([f for f in requests.get("https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json").json() 
                          if "flux" in f and f["flux"] > 1e-5])
        }
    except: return {"kp":0, "speed":0, "flares":0}

# ============================================================================
# 6. HURRICANES
# ============================================================================
def fetch_hurricanes():
    try:
        r = requests.get("https://www.nhc.noaa.gov/CurrentStorms.json", timeout=10).json()
        return [{"name": s["name"], "cat": s.get("classification","TD"), "wind": s.get("windSpeed",0)} 
                for s in r.get("activeStorms",[])]
    except: return []

# ============================================================================
# 7. PDF EXPORT
# ============================================================================
def make_pdf(lat, lon, eq_df, weather, alerts, space):
    if not REPORTLAB: return None
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter
    y = h - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "PanditaData Disaster Report"); y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Location: {rev_geocode(lat, lon)}"); y -= 20
    c.drawString(50, y, f"Generated: {datetime.now():%Y-%m-%d %H:%M}"); y -= 40

    c.drawString(50, y, "Earthquakes:"); y -= 20
    for _, r in eq_df.head(3).iterrows():
        c.drawString(70, y, f"{r['time']:%m-%d %H:%M} | M{r['mag']} | {r['dist']}km"); y -= 18

    if weather:
        y -= 10; c.drawString(50, y, "Weather:"); y -= 18
        c.drawString(70, y, f"{weather['current_weather']['temperature']}°C, {weather['current_weather']['windspeed']} km/h")

    if alerts:
        y -= 10; c.drawString(50, y, "NWS Alerts:"); y -= 18
        for a in alerts[:2]:
            c.drawString(70, y, f"{a['event']}: {a['headline'][:60]}"); y -= 18

    c.drawString(50, y-20, f"Space Weather: Kp={space['kp']}, Flares={space['flares']}")
    c.save(); buf.seek(0)
    return buf.getvalue()

# ============================================================================
# 8. SIDEBAR
# ============================================================================
with st.sidebar:
    st.image("https://via.placeholder.com/200x60.png?text=PanditaData", width=200)
    st.markdown("### Disaster Intelligence")

    if not login():
        st.stop()

    st.subheader("Saved Locations")
    sel = st.selectbox("Load", [""] + [s["name"] for s in st.session_state.saved])
    if sel:
        for s in st.session_state.saved:
            if s["name"] == sel:
                st.session_state.lat = s["lat"]
                st.session_state.lon = s["lon"]
                st.rerun()

    name = st.text_input("Save current as:")
    if st.button("Save") and name:
        save_loc(name)

    method = st.radio("Input", ["City", "Coords"])
    if method == "City":
        q = st.text_input("City/Address")
        if q and GEOPY:
            loc = geocode(q)
            if loc:
                st.session_state.lat = loc["lat"]
                st.session_state.lon = loc["lon"]
                st.success(loc["addr"])
    else:
        c1, c2 = st.columns(2)
        st.session_state.lat = c1.number_input("Lat", value=st.session_state.lat, format="%.6f")
        st.session_state.lon = c2.number_input("Lon", value=st.session_state.lon, format="%.6f")

    radius = st.slider("Radius (km)", 50, 1000, 300)
    days = st.slider("Days", 1, 30, 7)
    min_mag = st.slider("Min Mag", 0.0, 6.0, 2.0, 0.1)

# ============================================================================
# 9. MAIN DASHBOARD
# ============================================================================
lat, lon = st.session_state.lat, st.session_state.lon
st.title(f"Disaster Report: {rev_geocode(lat, lon)}")
st.markdown(f"**Lat:** {lat:.4f} | **Lon:** {lon:.4f} | **Radius:** {radius} km")

start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
end = datetime.now().strftime("%Y-%m-%d")

# --- EARTHQUAKES ---
with st.spinner("Earthquakes..."):
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
    st.info(f"**Aftershock Risk**: {ash['rec']} | {ash['prob']}% chance of M>{main['mag']-1:.1f} in 7 days")

    if PLOTLY:
        fig = px.scatter_mapbox(df, lat="dist", lon="dist", color="mag", size="mag",
                                hover_name="place", zoom=4, height=500, mapbox_style="open-street-map")
        fig.add_trace(go.Scattermapbox(lat=[lat], lon=[lon], marker=dict(color="blue", size=15), name="You"))
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df.head(10))

# --- WEATHER ---
with st.spinner("Weather..."):
    w = fetch_weather(lat, lon)
if w:
    cw = w["current_weather"]
    st.subheader("Current Weather")
    c1, c2 = st.columns(2)
    c1.metric("Temperature", f"{cw['temperature']:.1f}°C")
    c2.metric("Wind", f"{cw['windspeed']:.0f} km/h")

# --- NWS ALERTS ---
with st.spinner("NWS Alerts..."):
    alerts = fetch_alerts(lat, lon)
if alerts:
    st.subheader("NWS Severe Alerts")
    for a in alerts:
        sev = a["severity"].lower()
        cls = "critical-alert" if sev == "extreme" else "high-alert" if sev == "severe" else "moderate-alert"
        st.markdown(f"<div class='{cls}'>{a['event']}: {a['headline']}</div>", unsafe_allow_html=True)

# --- SPACE WEATHER ---
with st.spinner("Space Weather..."):
    space = fetch_space()
st.subheader("Space Weather")
c1, c2, c3 = st.columns(3)
c1.metric("Kp Index", f"{space['kp']:.1f}")
c2.metric("Solar Wind", f"{space['speed']:.0f} km/s")
c3.metric("Flares (24h)", space["flares"])

# --- HURRICANES ---
with st.spinner("Hurricanes..."):
    hur = fetch_hurricanes()
if hur:
    st.subheader("Active Hurricanes")
    for h in hur:
        st.metric(h["name"], f"{h['cat']} | {h['wind']} kt")

# --- PDF ---
if st.button("Download PDF Report"):
    pdf = make_pdf(lat, lon, df, w, alerts, space)
    if pdf:
        b64 = base64.b64encode(pdf).decode()
        st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="report.pdf">Download PDF</a>', unsafe_allow_html=True)
    else:
        st.error("PDF generation failed")

st.markdown("<div class='footer'>© 2025 PanditaData | Professional Disaster Intelligence</div>", unsafe_allow_html=True)
