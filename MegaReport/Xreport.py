# app.py
"""
Location-Based Disaster Report Generator
Streamlit-Cloud-ready version – uses pdfkit (wkhtmltopdf) instead of weasyprint.
Fixed: Default dates to past 30 days to avoid future API errors.
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
import os
import json
import hashlib

# ----------------------------------------------------------------------
# PAGE CONFIG & CSS
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Disaster Report Generator",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

def inject_custom_css(primary_color, secondary_color, background_color):
    st.markdown(f"""
    <style>
    :root {{ --primary-color: {primary_color}; --secondary-color: {secondary_color}; }}
    .stApp {{ background: {background_color}; }}
    h1, h2, h3 {{ color: var(--primary-color); }}
    .stButton>button {{ background-color: var(--primary-color); color: white; }}
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
def geocode_location(city_name):
    geolocator = Nominatim(user_agent="disaster_report_app_v1")
    try:
        loc = geolocator.geocode(city_name)
        return (loc.latitude, loc.longitude) if loc else (None, None)
    except Exception:
        return None, None

# ----------------------------------------------------------------------
# DATA FETCHERS (cached)
# ----------------------------------------------------------------------
@st.cache_data(ttl=1800)
def fetch_earthquakes(lat, lon, start, end, max_radius=1000):
    # Validate dates: end cannot exceed current date
    current_date = datetime.now().date()
    if end.date() > current_date:
        end = current_date
        st.warning(f"End date adjusted to today ({end.strftime('%Y-%m-%d')}) to avoid API errors.")
    if start.date() > end.date():
        start = end - timedelta(days=30)
        st.warning(f"Start date adjusted to {start.strftime('%Y-%m-%d')}.")
    
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": start.strftime("%Y-%m-%d"),
        "endtime": end.strftime("%Y-%m-%d"),
        "latitude": lat,
        "longitude": lon,
        "maxradiuskm": max_radius,
        "orderby": "time-desc",
        "limit": 200,
    }
    headers = {"User-Agent": "DisasterReportApp/1.0 (contact@example.com)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        feats = r.json().get("features", [])
        rows = []
        for f in feats:
            p = f["properties"]
            c = f["geometry"]["coordinates"]
            dist = haversine(lat, lon, c[1], c[0])
            rows.append({
                "time": datetime.fromtimestamp(p["time"]/1000),
                "magnitude": p["mag"],
                "depth": c[2],
                "place": p["place"],
                "distance_km": round(dist, 2),
                "lat": c[1],
                "lon": c[0],
            })
        return pd.DataFrame(rows)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            st.error("Invalid query parameters. Please check date range (cannot include future dates).")
        else:
            st.error(f"Earthquake API error: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Earthquake API error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def get_grid(lat, lon):
    url = f"https://api.weather.gov/points/{lat},{lon}"
    headers = {"User-Agent": "DisasterReportApp/1.0 (contact@example.com)"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()["properties"]
        return data["forecast"], (data["gridId"], data["gridX"], data["gridY"])
    except Exception as e:
        st.warning(f"NOAA grid fetch failed (US-only): {e}. Falling back to empty forecast.")
        return None, None

@st.cache_data(ttl=1800)
def fetch_forecast(url):
    if not url:
        return pd.DataFrame()
    headers = {"User-Agent": "DisasterReportApp/1.0 (contact@example.com)"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        periods = r.json()["properties"]["periods"][:14]
        rows = []
        for p in periods:
            rows.append({
                "name": p["name"],
                "temperature": p["temperature"],
                "windSpeed": p["windSpeed"],
                "shortForecast": p["shortForecast"],
                "precip": p.get("probabilityOfPrecipitation", {}).get("value", 0),
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=900)
def fetch_alerts(lat, lon, country="US"):
    url = "https://api.weather.gov/alerts/active"
    params = {"point": f"{lat},{lon}"}
    if country != "US":
        st.warning("Alerts are US-only; using general query.")
    headers = {"User-Agent": "DisasterReportApp/1.0 (contact@example.com)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        feats = r.json().get("features", [])
        rows = []
        for f in feats:
            p = f["properties"]
            rows.append({
                "event": p["event"],
                "severity": p["severity"],
                "urgency": p["urgency"],
                "areaDesc": p["areaDesc"],
                "description": p["description"][:500],
                "effective": p["effective"],
                "expires": p["expires"],
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

# ----------------------------------------------------------------------
# MAP HELPERS
# ----------------------------------------------------------------------
def make_map(lat, lon, quakes=None, alerts=None):
    m = folium.Map(location=[lat, lon], zoom_start=7)
    folium.Marker([lat, lon], popup="Selected Location", icon=folium.Icon(color="red")).add_to(m)

    if quakes is not None and not quakes.empty:
        for _, q in quakes.iterrows():
            color = "red" if q["magnitude"] >= 5 else "orange" if q["magnitude"] >= 3 else "green"
            folium.CircleMarker(
                [q["lat"], q["lon"]],
                radius=max(5, q["magnitude"] * 2),
                color=color,
                fill=True,
                popup=f"M{q['magnitude']} | {q['time'].strftime('%m/%d %H:%M')} | {q['distance_km']}km",
            ).add_to(m)

    if alerts is not None and not alerts.empty:
        for _ in alerts.itertuples():
            folium.Marker(
                [lat, lon],
                icon=folium.Icon(color="purple", icon="warning"),
                popup="Warning: Active Alert",
            ).add_to(m)
    return m

# ----------------------------------------------------------------------
# PDF GENERATION (pdfkit)
# ----------------------------------------------------------------------
def fig_to_png_base64(fig):
    buf = BytesIO()
    fig.write_image(buf, format="png", engine="kaleido")
    return base64.b64encode(buf.getvalue()).decode()

def map_to_png_base64(m):
    img = m._to_png()
    return base64.b64encode(img).decode()

def build_pdf_html(title, loc_name, quakes_df, forecast_df, alerts_df, prim, sec):
    date_str = "October 25, 2025"

    # ---- static assets -------------------------------------------------
    map_b64 = None
    try:
        if not quakes_df.empty or not alerts_df.empty:
            map_b64 = map_to_png_base64(make_map(st.session_state.lat, st.session_state.lon, quakes_df, alerts_df))
    except Exception as e:
        st.warning(f"Map PNG generation failed for PDF: {e}. Skipping map in PDF.")

    pie_b64 = None
    try:
        if not quakes_df.empty:
            bins = [0, 10, 100, 500, 1000]
            labels = ["0-10km", "11-100km", "101-500km", ">500km"]
            quakes_df["bin"] = pd.cut(quakes_df["distance_km"], bins=bins, labels=labels, include_lowest=True)
            counts = quakes_df["bin"].value_counts().reindex(labels, fill_value=0)
            fig = px.pie(values=counts.values, names=counts.index,
                         color_discrete_sequence=[prim, sec])
            pie_b64 = fig_to_png_base64(fig)
    except Exception:
        pass

    # ---- HTML ---------------------------------------------------------
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{font-family: Arial, Helvetica, sans-serif; margin: 1in; line-height: 1.5;}}
            h1 {{color: {prim}; text-align:center;}}
            h2 {{color: {sec}; border-bottom:2px solid #ddd; padding-bottom:5px;}}
            table {{width:100%; border-collapse:collapse; margin:15px 0;}}
            th, td {{border:1px solid #ddd; padding:8px; text-align:left;}}
            th {{background:#f4f4f4;}}
            img {{max-width:100%; height:auto; display:block; margin:20px auto;}}
            .footer {{position:fixed; bottom:0; left:0; right:0; text-align:center; font-size:10px;}}
            .page-break {{ page-break-after: always; }}
        </style>
    </head>
    <body>
        <div style="text-align:center; margin-top:120px;">
            <h1>Earthquake & Weather Report</h1>
            <h2>{loc_name}</h2>
            <p><strong>Generated on:</strong> {date_str}</p>
        </div>
        <div class="footer">Confidential – Page <span class="page">1</span></div>

        <div class="page-break"></div>

        <h2>Executive Summary</h2>
        <p><strong>Location:</strong> {loc_name} ({st.session_state.lat:.4f}, {st.session_state.lon:.4f})</p>
        <p><strong>Period:</strong> {st.session_state.start_date.strftime('%Y-%m-%d')} to {st.session_state.end_date.strftime('%Y-%m-%d')}</p>
        <p><strong>Earthquakes:</strong> {len(quakes_df)} | <strong>Alerts:</strong> {len(alerts_df)}</p>
    """
    if pie_b64:
        html += f'<img src="data:image/png;base64,{pie_b64}" />'
    if map_b64:
        html += f'<div class="page-break"></div><img src="data:image/png;base64,{map_b64}" />'

    html += """
        <div class="page-break"></div>
        <h2>Earthquakes (Top 10)</h2>
    """
    if not quakes_df.empty:
        top = quakes_df.head(10)[["time","magnitude","distance_km","place"]].copy()
        top["time"] = top["time"].dt.strftime("%Y-%m-%d %H:%M")
        html += top.to_html(index=False)

    html += """
        <div class="page-break"></div>
        <h2>7-Day Forecast</h2>
    """
    if not forecast_df.empty:
        html += forecast_df[["name","temperature","shortForecast"]].to_html(index=False)

    html += """
        <div class="page-break"></div>
        <h2>Active Alerts</h2>
    """
    if not alerts_df.empty:
        html += alerts_df[["event","severity","areaDesc"]].to_html(index=False)
    else:
        html += "<p>No active alerts.</p>"

    html += "</body></html>"
    return html

# ----------------------------------------------------------------------
# MAIN APP
# ----------------------------------------------------------------------
def main():
    st.title("Location-Based Disaster Report Generator")
    st.markdown("Real-time USGS + NOAA data • Interactive charts • **PDF export**")

    # ------------------- SIDEBAR -------------------
    with st.sidebar:
        st.header("Configuration")
        mode = st.radio("Location input", ["Coordinates", "City name"])

        if mode == "Coordinates":
            lat = st.number_input("Latitude", value=37.7749, format="%.6f")
            lon = st.number_input("Longitude", value=-122.4194, format="%.6f")
            loc_name = f"Custom ({lat:.4f}, {lon:.4f})"
        else:
            city = st.text_input("City", "San Francisco")
            if st.button("Geocode"):
                with st.spinner("Geocoding..."):
                    lat, lon = geocode_location(city)
                    if lat:
                        st.success(f"{lat:.4f}, {lon:.4f}")
                        loc_name = city
                    else:
                        st.error("Not found")
                        lat, lon = 37.7749, -122.4194
                        loc_name = "San Francisco"
            else:
                lat, lon = 37.7749, -122.4194
                loc_name = "San Francisco"

        country = st.selectbox("Country", ["US", "CA", "MX"], index=0)

        # Default to past 30 days to avoid future dates
        default_start = datetime.now() - timedelta(days=30)
        default_end = datetime.now()

        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("Start", default_start)
        with col2:
            end = st.date_input("End", default_end)

        st.header("Theme")
        prim = st.color_picker("Primary", "#FF6B6B")
        sec = st.color_picker("Secondary", "#4ECDC4")
        bg = st.color_picker("Background", "#FFFFFF")
        inject_custom_css(prim, sec, bg)

    # store in session_state for PDF generation
    st.session_state.update({
        "lat": lat, "lon": lon, "location_name": loc_name,
        "start_date": start, "end_date": end,
        "country": country, "primary": prim, "secondary": sec,
    })

    # ------------------- MAP PREVIEW -------------------
    st.subheader("Location preview")
    preview = folium.Map(location=[lat, lon], zoom_start=9)
    folium.Marker([lat, lon], popup=loc_name).add_to(preview)
    folium_static(preview, width=700, height=300)

    # ------------------- FETCH DATA -------------------
    with st.spinner("Earthquakes..."):
        quakes = fetch_earthquakes(lat, lon, start, end)
    with st.spinner("Weather grid..."):
        forecast_url, _ = get_grid(lat, lon)
    with st.spinner("Forecast..."):
        forecast = fetch_forecast(forecast_url)
    with st.spinner("Alerts..."):
        alerts = fetch_alerts(lat, lon, country)

    # ------------------- TABS -------------------
    t1, t2, t3, t4 = st.tabs(["Executive Summary", "Earthquakes", "Weather", "Alerts"])

    # ---- Executive Summary ----
    with t1:
        st.header(f"Report – {loc_name}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Earthquakes", len(quakes))
        c2.metric("Alerts", len(alerts))
        avg_temp = forecast["temperature"].head(6).mean() if not forecast.empty else 0
        c3.metric("Avg Temp (3 d)", f"{avg_temp:.1f}°F")
        risk = "High" if len(quakes) > 5 or len(alerts) > 0 else "Low"
        c4.metric("Risk", risk)

        col1, col2 = st.columns(2)
        with col1:
            if not quakes.empty:
                bins = [0, 10, 100, 500, 1000]
                labels = ["0-10km", "11-100km", "101-500km", ">500km"]
                quakes["bin"] = pd.cut(quakes["distance_km"], bins=bins, labels=labels)
                fig = px.pie(quakes["bin"].value_counts(), names=labels,
                             color_discrete_sequence=[prim, sec])
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if not forecast.empty:
                daily = forecast[::2].head(7)
                fig = px.line(daily, x="name", y="temperature", markers=True,
                              line_shape="spline")
                fig.update_traces(line_color=sec)
                st.plotly_chart(fig, use_container_width=True)

        m = make_map(lat, lon, quakes, alerts)
        folium_static(m, width=700, height=450)

    # ---- Earthquakes ----
    with t2:
        if quakes.empty:
            st.info("No earthquakes in range.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Strongest", f"M{quakes['magnitude'].max():.1f}")
            c2.metric("Avg Depth", f"{quakes['depth'].mean():.1f} km")
            c3.metric("≤100 km", len(quakes[quakes["distance_km"] <= 100]))

            col1, col2 = st.columns(2)
            with col1:
                fig = px.scatter(quakes, x="time", y="magnitude", size="distance_km")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.histogram(quakes, x="magnitude", nbins=20,
                                   color_discrete_sequence=[prim])
                st.plotly_chart(fig, use_container_width=True)

            m = make_map(lat, lon, quakes)
            folium_static(m, width=700, height=400)

            disp = quakes[["time","magnitude","distance_km","place"]].copy()
            disp["time"] = disp["time"].dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(disp.head(20), use_container_width=True)

    # ---- Weather ----
    with t3:
        if forecast.empty:
            st.info("NOAA data unavailable (US-only).")
        else:
            cur = forecast.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Current", f"{cur['temperature']}°F")
            c2.metric("Wind", cur["windSpeed"])
            c3.metric("Precip", f"{cur['precip']}%")

            fig = go.Figure()
            daily = forecast[::2].head(7)
            fig.add_trace(go.Scatter(x=daily["name"], y=daily["temperature"],
                                     mode="lines+markers", name="Temp"))
            fig.update_layout(title="7-Day Temperature")
            st.plotly_chart(fig, use_container_width=True)

            tbl = forecast[["name","temperature","shortForecast","windSpeed","precip"]].copy()
            tbl.rename(columns={"name":"Day","temperature":"Temp °F","shortForecast":"Conditions",
                                "windSpeed":"Wind","precip":"Precip %"}, inplace=True)
            st.dataframe(tbl, use_container_width=True)

    # ---- Alerts ----
    with t4:
        if alerts.empty:
            st.success("No active alerts.")
        else:
            c1, c2 = st.columns(2)
            c1.metric("Total", len(alerts))
            c2.metric("Severe", len(alerts[alerts["severity"]=="Severe"]))

            fig = px.pie(alerts, names="event", color_discrete_sequence=[prim, sec])
            st.plotly_chart(fig, use_container_width=True)

            for a in alerts.itertuples():
                with st.expander(f"{a.event} – {a.severity}"):
                    st.write(f"**Area:** {a.areaDesc}")
                    st.write(f"**Effective:** {a.effective} | **Expires:** {a.expires}")
                    st.write(a.description)

    # ------------------- PDF EXPORT -------------------
    if st.button("Generate & Download PDF Report", type="primary"):
        with st.spinner("Building PDF..."):
            try:
                html_str = build_pdf_html(
                    "Disaster Report", loc_name, quakes, forecast, alerts,
                    st.session_state.primary, st.session_state.secondary,
                )
                # pdfkit options – works on Streamlit Cloud
                config = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")
                pdf_bytes = pdfkit.from_string(
                    html_str,
                    False,
                    configuration=config,
                    options={
                        "page-size": "Letter",
                        "margin-top": "0.75in",
                        "margin-right": "0.75in",
                        "margin-bottom": "0.75in",
                        "margin-left": "0.75in",
                        "encoding": "UTF-8",
                        "no-outline": None,
                        "enable-local-file-access": None,
                    },
                )
                b64 = base64.b64encode(pdf_bytes).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="{loc_name.replace(" ", "_")}_Report_2025-10-25.pdf">Download PDF now</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.success("PDF ready!")
            except Exception as e:
                st.error(f"PDF generation failed: {e}")

if __name__ == "__main__":
    main()
