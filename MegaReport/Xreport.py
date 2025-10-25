# app.py
"""
Location-Based Disaster Report Generator
Streamlit-Cloud-ready • No Selenium • No WeasyPrint • Full Consistency
"""

import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import numpy as np
import base64
from io import BytesIO
import pdfkit

# ----------------------------------------------------------------------
# PAGE CONFIG & CSS
# ----------------------------------------------------------------------
st.set_page_config(page_title="Disaster Report", page_icon="globe", layout="wide")

def inject_css(primary, secondary, bg):
    st.markdown(f"""
    <style>
    :root {{ --primary: {primary}; --secondary: {secondary}; }}
    .stApp {{ background: {bg}; }}
    h1, h2, h3 {{ color: var(--primary); }}
    .stButton>button {{ background: var(--primary); color: white; }}
    </style>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

@st.cache_data(ttl=3600)
def geocode(city):
    try:
        loc = Nominatim(user_agent="disaster_app").geocode(city)
        return (loc.latitude, loc.longitude) if loc else (None, None)
    except:
        return None, None

# ----------------------------------------------------------------------
# DATA: EARTHQUAKES (FIXED DATE LOGIC)
# ----------------------------------------------------------------------
@st.cache_data(ttl=1800)
def fetch_earthquakes(lat, lon, start_date, end_date, radius=1000):
    today = datetime.now().date()
    
    # FIX: start_date and end_date are date objects → no .date()
    if end_date > today:
        st.warning(f"End date capped to today: {today}")
        end_date = today
    if start_date > end_date:
        st.warning("Start > End → using last 30 days")
        start_date = today - timedelta(days=30)

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": start_date.isoformat(),
        "endtime": end_date.isoformat(),
        "latitude": lat,
        "longitude": lon,
        "maxradiuskm": radius,
        "orderby": "time-desc",
        "limit": 200
    }
    headers = {"User-Agent": "DisasterReport/1.0"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=12)
        r.raise_for_status()
        feats = r.json().get("features", [])
        rows = []
        for f in feats:
            p = f["properties"]
            c = f["geometry"]["coordinates"]
            dist = haversine(lat, lon, c[1], c[0])
            rows.append({
                "time": datetime.fromtimestamp(p["time"]/1000),
                "mag": p["mag"],
                "depth": c[2],
                "place": p["place"],
                "dist_km": round(dist, 1),
                "lat": c[1], "lon": c[0]
            })
        return pd.DataFrame(rows)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            st.error("Bad request: Check dates (cannot be future).")
        else:
            st.error(f"API error: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return pd.DataFrame()

# ----------------------------------------------------------------------
# DATA: WEATHER (US-only)
# ----------------------------------------------------------------------
@st.cache_data(ttl=1800)
def get_noaa_grid(lat, lon):
    try:
        r = requests.get(f"https://api.weather.gov/points/{lat},{lon}", timeout=10)
        r.raise_for_status()
        data = r.json()["properties"]
        return data["forecast"]
    except:
        return None

@st.cache_data(ttl=1800)
def fetch_forecast(url):
    if not url:
        return pd.DataFrame()
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        periods = r.json()["properties"]["periods"][:14]
        return pd.DataFrame([
            {
                "name": p["name"],
                "temp": p["temperature"],
                "wind": p["windSpeed"],
                "cond": p["shortForecast"],
                "precip": p.get("probabilityOfPrecipitation", {}).get("value", 0)
            } for p in periods
        ])
    except:
        return pd.DataFrame()

@st.cache_data(ttl=900)
def fetch_alerts(lat, lon):
    try:
        r = requests.get(f"https://api.weather.gov/alerts/active?point={lat},{lon}", timeout=10)
        r.raise_for_status()
        feats = r.json().get("features", [])
        return pd.DataFrame([
            {
                "event": f["properties"]["event"],
                "severity": f["properties"]["severity"],
                "area": f["properties"]["areaDesc"],
                "desc": f["properties"]["description"][:300]
            } for f in feats
        ])
    except:
        return pd.DataFrame()

# ----------------------------------------------------------------------
# MAP
# ----------------------------------------------------------------------
def make_map(lat, lon, quakes=None, alerts=None):
    m = folium.Map(location=[lat, lon], zoom_start=7)
    folium.Marker([lat, lon], popup="Location", icon=folium.Icon(color="red")).add_to(m)
    if quakes is not None and not quakes.empty:
        for _, q in quakes.iterrows():
            color = "red" if q["mag"] >= 5 else "orange" if q["mag"] >= 3 else "green"
            folium.CircleMarker(
                [q["lat"], q["lon"]], radius=max(5, q["mag"]*2), color=color, fill=True,
                popup=f"M{q['mag']} | {q['time'].strftime('%m/%d %H:%M')} | {q['dist_km']}km"
            ).add_to(m)
    return m

# ----------------------------------------------------------------------
# PDF (NO MAP PNG → NO SELENIUM)
# ----------------------------------------------------------------------
def fig_to_b64(fig):
    return base64.b64encode(fig.to_image(format="png", engine="kaleido")).decode()

def build_pdf_html(loc_name, quakes, forecast, alerts, prim, sec):
    date_str = "October 25, 2025"
    pie_b64 = None
    if not quakes.empty:
        bins = [0, 10, 100, 500, 1000]
        labels = ["0-10km", "11-100km", "101-500km", ">500km"]
        quakes["bin"] = pd.cut(quakes["dist_km"], bins=bins, labels=labels)
        fig = px.pie(quakes["bin"].value_counts(), names=labels, color_discrete_sequence=[prim, sec])
        pie_b64 = fig_to_b64(fig)

    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8">
    <style>
        body {{font-family: Arial; margin: 1in; line-height: 1.6;}}
        h1 {{color: {prim}; text-align: center;}}
        h2 {{color: {sec}; border-bottom: 1px solid #ccc;}}
        table {{width:100%; border-collapse: collapse; margin: 15px 0;}}
        th, td {{border: 1px solid #ddd; padding: 8px; text-align: left;}}
        th {{background: #f8f8f8;}}
        img {{max-width: 100%; margin: 20px auto; display: block;}}
        .page-break {{page-break-after: always;}}
    </style></head><body>

    <h1>Earthquake & Weather Report</h1>
    <h2 style="text-align:center">{loc_name}</h2>
    <p style="text-align:center"><strong>Generated:</strong> {date_str}</p>

    <div class="page-break"></div>
    <h2>Summary</h2>
    <p><strong>Location:</strong> {loc_name} ({st.session_state.lat:.4f}, {st.session_state.lon:.4f})</p>
    <p><strong>Period:</strong> {st.session_state.start_date} to {st.session_state.end_date}</p>
    <p><strong>Quakes:</strong> {len(quakes)} | <strong>Alerts:</strong> {len(alerts)}</p>
    """
    if pie_b64:
        html += f'<img src="data:image/png;base64,{pie_b64}">'
    html += '<div class="page-break"></div><h2>Top Earthquakes</h2>'
    if not quakes.empty:
        top = quakes.head(10)[["time","mag","dist_km","place"]].copy()
        top["time"] = top["time"].dt.strftime("%Y-%m-%d %H:%M")
        html += top.to_html(index=False)
    html += '<div class="page-break"></div><h2>7-Day Forecast</h2>'
    if not forecast.empty:
        html += forecast[["name","temp","cond"]].to_html(index=False)
    html += '<div class="page-break"></div><h2>Alerts</h2>'
    html += alerts[["event","severity","area"]].to_html(index=False) if not alerts.empty else "<p>None</p>"
    html += "</body></html>"
    return html

# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    st.title("Disaster Report Generator")
    st.markdown("USGS + NOAA • Interactive • PDF Export")

    # === SIDEBAR ===
    with st.sidebar:
        st.header("Settings")
        mode = st.radio("Input", ["City", "Coords"])
        if mode == "City":
            city = st.text_input("City", "San Francisco")
            if st.button("Geocode"):
                with st.spinner("Finding..."):
                    lat, lon = geocode(city)
                    if lat:
                        st.success(f"{lat:.4f}, {lon:.4f}")
                        st.session_state.lat, st.session_state.lon = lat, lon
                        st.session_state.loc_name = city
                    else:
                        st.error("Not found")
            lat, lon = st.session_state.get("lat", 37.7749), st.session_state.get("lon", -122.4194)
            loc_name = st.session_state.get("loc_name", "San Francisco")
        else:
            lat = st.number_input("Lat", value=37.7749, format="%.6f")
            lon = st.number_input("Lon", value=-122.4194, format="%.6f")
            loc_name = f"Custom ({lat:.4f}, {lon:.4f})"

        today = datetime.now().date()
        default_start = today - timedelta(days=30)
        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("Start", default_start)
        with col2:
            end = st.date_input("End", today)

        prim = st.color_picker("Primary", "#FF6B6B")
        sec = st.color_picker("Secondary", "#4ECDC4")
        bg = st.color_picker("BG", "#FFFFFF")
        inject_css(prim, sec, bg)

    # === UPDATE SESSION STATE ===
    st.session_state.update({
        "lat": lat, "lon": lon, "loc_name": loc_name,
        "start_date": start, "end_date": end,
        "primary": prim, "secondary": sec
    })

    # === MAP PREVIEW ===
    st.subheader("Location")
    preview = folium.Map(location=[lat, lon], zoom_start=9)
    folium.Marker([lat, lon], popup=loc_name).add_to(preview)
    folium_static(preview, width=700, height=300)

    # === FETCH DATA ===
    with st.spinner("Earthquakes..."):
        quakes = fetch_earthquakes(lat, lon, start, end)
    with st.spinner("Weather..."):
        forecast = fetch_forecast(get_noaa_grid(lat, lon))
    with st.spinner("Alerts..."):
        alerts = fetch_alerts(lat, lon)

    # === TABS ===
    t1, t2, t3, t4 = st.tabs(["Summary", "Quakes", "Weather", "Alerts"])

    with t1:
        st.header(loc_name)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Quakes", len(quakes))
        c2.metric("Alerts", len(alerts))
        c3.metric("Avg Temp", f"{forecast['temp'].head(6).mean():.1f}°F" if not forecast.empty else "N/A")
        c4.metric("Risk", "High" if len(quakes) > 5 or len(alerts) > 0 else "Low")

        col1, col2 = st.columns(2)
        with col1:
            if not quakes.empty:
                bins = [0, 10, 100, 500, 1000]
                labels = ["0-10km", "11-100km", "101-500km", ">500km"]
                quakes["bin"] = pd.cut(quakes["dist_km"], bins=bins, labels=labels)
                fig = px.pie(quakes["bin"].value_counts(), names=labels, color_discrete_sequence=[prim, sec])
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if not forecast.empty:
                daily = forecast[::2].head(7)
                fig = px.line(daily, x="name", y="temp", markers=True, line_shape="spline")
                fig.update_traces(line_color=sec)
                st.plotly_chart(fig, use_container_width=True)

        folium_static(make_map(lat, lon, quakes, alerts), width=700, height=450)

    with t2:
        if quakes.empty:
            st.info("No quakes")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Max Mag", f"M{quakes['mag'].max():.1f}")
            c2.metric("Avg Depth", f"{quakes['depth'].mean():.1f}km")
            c3.metric("≤100km", len(quakes[quakes["dist_km"] <= 100]))
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.scatter(quakes, x="time", y="mag", size="dist_km"), use_container_width=True)
            with col2:
                st.plotly_chart(px.histogram(quakes, x="mag", nbins=20, color_discrete_sequence=[prim]), use_container_width=True)
            folium_static(make_map(lat, lon, quakes), width=700, height=400)
            disp = quakes[["time","mag","dist_km","place"]].copy()
            disp["time"] = disp["time"].dt.strftime("%m/%d %H:%M")
            st.dataframe(disp.head(20), use_container_width=True)

    with t3:
        if forecast.empty:
            st.info("Weather: US-only")
        else:
            cur = forecast.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Now", f"{cur['temp']}°F")
            c2.metric("Wind", cur["wind"])
            c3.metric("Precip", f"{cur['precip']}%")
            fig = go.Figure(go.Scatter(x=forecast[::2].head(7)["name"], y=forecast[::2].head(7)["temp"], mode="lines+markers"))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(forecast[["name","temp","cond","precip"]], use_container_width=True)

    with t4:
        if alerts.empty:
            st.success("No alerts")
        else:
            st.metric("Total", len(alerts))
            st.plotly_chart(px.pie(alerts, names="event", color_discrete_sequence=[prim, sec]), use_container_width=True)
            for a in alerts.itertuples():
                with st.expander(f"{a.event}"):
                    st.write(f"**Area:** {a.area}<br>**Desc:** {a.desc}", unsafe_allow_html=True)

    # === PDF ===
    if st.button("Generate PDF", type="primary"):
        with st.spinner("Creating PDF..."):
            try:
                html = build_pdf_html(loc_name, quakes, forecast, alerts, prim, sec)
                config = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")
                pdf = pdfkit.from_string(html, False, configuration=config, options={
                    "page-size": "Letter", "margin-top": "0.75in", "margin-bottom": "0.75in",
                    "margin-left": "0.75in", "margin-right": "0.75in", "encoding": "UTF-8"
                })
                b64 = base64.b64encode(pdf).decode()
                st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="{loc_name}_Report.pdf">Download PDF</a>', unsafe_allow_html=True)
                st.success("Done!")
            except Exception as e:
                st.error(f"PDF failed: {e}")

if __name__ == "__main__":
    main()
