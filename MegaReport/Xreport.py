# app.py
"""
Location-Based Disaster Report Generator
A production-ready Streamlit app for interactive earthquake, weather, and alert reports.
Features real-time USGS/NOAA data, customizable themes, interactive maps/charts, and PDF export.
Deployable on Streamlit Community Cloud.
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
from geopy.exc import GeocoderTimedOut
import numpy as np
import base64
from io import BytesIO
import pdfkit
import weasyprint
from weasyprint import HTML
import os
import json
import hashlib

# === CONFIGURATION ===
st.set_page_config(
    page_title="Disaster Report Generator",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === REQUIREMENTS NOTE ===
# Save this as requirements.txt in your GitHub repo:
"""
streamlit>=1.30.0
folium>=0.14.0
streamlit-folium>=0.13.0
plotly>=5.15.0
pandas>=1.5.0
geopy>=2.3.0
requests>=2.28.0
pdfkit>=1.0.0
weasyprint>=59.0
"""

# === CUSTOM CSS INJECTION FOR THEMES ===
def inject_custom_css(primary_color, secondary_color, background_color):
    st.markdown(f"""
    <style>
    :root {{
        --primary-color: {primary_color};
        --secondary-color: {secondary_color};
    }}
    .reportview-container {{
        background: {background_color};
    }}
    .stApp {{
        background: {background_color};
    }}
    h1, h2, h3 {{
        color: var(--primary-color);
    }}
    .stButton>button {{
        background-color: var(--primary-color);
        color: white;
    }}
    .stMetric {{
        background-color: rgba(255, 107, 107, 0.1);
        padding: 10px;
        border-radius: 8px;
        border-left: 5px solid var(--primary-color);
    }}
    </style>
    """, unsafe_allow_html=True)

# === HELPER: Haversine Distance ===
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

# === GEOCODING ===
@st.cache_data(ttl=3600)
def geocode_location(city_name):
    geolocator = Nominatim(user_agent="disaster_report_app_v1.0_contact@example.com")
    try:
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except GeocoderTimedOut:
        st.warning("Geocoding timed out. Using default coordinates.")
        return 37.7749, -122.4194

# === DATA FETCHING: EARTHQUAKES ===
@st.cache_data(ttl=1800)
def fetch_earthquakes(lat, lon, start_date, end_date, max_radius=1000):
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": start_date.strftime("%Y-%m-%d"),
        "endtime": end_date.strftime("%Y-%m-%d"),
        "latitude": lat,
        "longitude": lon,
        "maxradiuskm": max_radius,
        "orderby": "time-desc",
        "limit": 200
    }
    headers = {"User-Agent": "DisasterReportApp/1.0 (contact@example.com)"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        features = data.get("features", [])
        
        quakes = []
        for f in features:
            props = f["properties"]
            coords = f["geometry"]["coordinates"]
            dist = haversine(lat, lon, coords[1], coords[0])
            quakes.append({
                "time": datetime.fromtimestamp(props["time"]/1000),
                "magnitude": props["mag"],
                "depth": coords[2],
                "place": props["place"],
                "distance_km": round(dist, 2),
                "lat": coords[1],
                "lon": coords[0]
            })
        return pd.DataFrame(quakes)
    except Exception as e:
        st.error(f"Earthquake API error: {str(e)}")
        return pd.DataFrame()

# === DATA FETCHING: WEATHER GRID ===
@st.cache_data(ttl=1800)
def get_weather_grid(lat, lon):
    url = f"https://api.weather.gov/points/{lat},{lon}"
    headers = {"User-Agent": "DisasterReportApp/1.0 (contact@example.com)"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        forecast_url = data["properties"]["forecast"]
        grid_data = data["properties"]["gridId"], data["properties"]["gridX"], data["properties"]["gridY"]
        return forecast_url, grid_data
    except Exception as e:
        st.warning(f"NOAA grid fetch failed: {str(e)}. Using fallback.")
        return None, None

# === DATA FETCHING: FORECAST ===
@st.cache_data(ttl=1800)
def fetch_forecast(forecast_url):
    if not forecast_url:
        return pd.DataFrame()
    headers = {"User-Agent": "DisasterReportApp/1.0 (contact@example.com)"}
    try:
        response = requests.get(forecast_url, headers=headers, timeout=10)
        response.raise_for_status()
        periods = response.json()["properties"]["periods"][:14]  # 7 days
        forecast = []
        for p in periods:
            forecast.append({
                "name": p["name"],
                "startTime": p["startTime"],
                "temperature": p["temperature"],
                "temperatureUnit": p["temperatureUnit"],
                "windSpeed": p["windSpeed"],
                "windDirection": p["windDirection"],
                "shortForecast": p["shortForecast"],
                "probabilityOfPrecipitation": p.get("probabilityOfPrecipitation", {}).get("value", 0)
            })
        return pd.DataFrame(forecast)
    except Exception as e:
        st.warning(f"Forecast fetch failed: {str(e)}")
        return pd.DataFrame()

# === DATA FETCHING: ALERTS ===
@st.cache_data(ttl=900)
def fetch_alerts(lat, lon, country="US"):
    url = "https://api.weather.gov/alerts/active"
    params = {"point": f"{lat},{lon}"}
    if country != "US":
        params["area"] = country
    headers = {"User-Agent": "DisasterReportApp/1.0 (contact@example.com)"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        features = response.json().get("features", [])
        alerts = []
        for f in features:
            p = f["properties"]
            alerts.append({
                "event": p["event"],
                "severity": p["severity"],
                "urgency": p["urgency"],
                "areaDesc": p["areaDesc"],
                "description": p["description"],
                "effective": p["effective"],
                "expires": p["expires"]
            })
        return pd.DataFrame(alerts)
    except Exception as e:
        st.warning(f"Alerts fetch failed: {str(e)}")
        return pd.DataFrame()

# === MAP GENERATION ===
def create_folium_map(lat, lon, quakes_df=None, alerts_df=None):
    m = folium.Map(location=[lat, lon], zoom_start=7, tiles="OpenStreetMap")
    folium.Marker([lat, lon], popup="Selected Location", icon=folium.Icon(color="red")).add_to(m)
    
    if quakes_df is not None and not quakes_df.empty:
        for _, q in quakes_df.iterrows():
            color = "red" if q["magnitude"] >= 5 else "orange" if q["magnitude"] >= 3 else "green"
            folium.CircleMarker(
                location=[q["lat"], q["lon"]],
                radius=max(5, q["magnitude"] * 2),
                color=color,
                fill=True,
                popup=f"M{q['magnitude']} | {q['time'].strftime('%Y-%m-%d %H:%M')} | {q['distance_km']}km"
            ).add_to(m)
    
    if alerts_df is not None and not alerts_df.empty:
        for _, a in alerts_df.iterrows():
            folium.Marker(
                [lat, lon],
                icon=folium.Icon(color="purple", icon="warning"),
                popup=f"<b>{a['event']}</b><br>{a['description'][:100]}..."
            ).add_to(m)
    
    return m

# === PDF UTILITIES ===
def fig_to_base64_png(fig):
    buf = BytesIO()
    fig.write_image(buf, format="png", engine="kaleido")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def folium_to_png(m):
    img_data = m._to_png()
    return base64.b64encode(img_data).decode()

def generate_pdf_html(title, location_name, quakes_df, forecast_df, alerts_df, primary_color, secondary_color):
    date_str = "October 25, 2025"
    
    # Static images
    map_img = None
    if not quakes_df.empty or not alerts_df.empty:
        m = create_folium_map(st.session_state.lat, st.session_state.lon, quakes_df, alerts_df)
        map_img = folium_to_png(m)

    pie_img = None
    if not quakes_df.empty:
        bins = [0, 10, 100, 500, 1000]
        labels = ["0-10km", "11-100km", "101-500km", ">500km"]
        quakes_df['bin'] = pd.cut(quakes_df['distance_km'], bins=bins, labels=labels, include_lowest=True)
        counts = quakes_df['bin'].value_counts().reindex(labels, fill_value=0)
        fig = px.pie(values=counts.values, names=counts.index, color_discrete_sequence=[primary_color, secondary_color])
        pie_img = fig_to_base64_png(fig)

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 1in; line-height: 1.5; }}
            h1 {{ color: {primary_color}; text-align: center; }}
            h2 {{ color: {secondary_color}; border-bottom: 2px solid #ccc; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .page-break {{ page-break-before: always; }}
            .footer {{ position: fixed; bottom: 0; left: 0; right: 0; text-align: center; font-size: 10px; }}
            img {{ max-width: 100%; height: auto; }}
        </style>
    </head>
    <body>
        <!-- Cover Page -->
        <div style="text-align:center; margin-top:100px;">
            <h1>Earthquake & Weather Report</h1>
            <h2>{location_name}</h2>
            <p><strong>Generated on:</strong> {date_str}</p>
        </div>
        <div class="footer">Confidential Report | Page <span class="page">1</span></div>
        <div class="page-break"></div>

        <!-- Executive Summary -->
        <h2>Executive Summary</h2>
        <p><strong>Location:</strong> {location_name} ({st.session_state.lat:.4f}, {st.session_state.lon:.4f})</p>
        <p><strong>Date Range:</strong> {st.session_state.start_date.strftime('%Y-%m-%d')} to {st.session_state.end_date.strftime('%Y-%m-%d')}</p>
        <p><strong>Total Earthquakes:</strong> {len(quakes_df)}</p>
        <p><strong>Active Alerts:</strong> {len(alerts_df)}</p>
    """
    
    if pie_img:
        html += f'<img src="data:image/png;base64,{pie_img}" style="width:50%; display:block; margin:20px auto;">'
    
    if map_img:
        html += f'<div class="page-break"></div><img src="data:image/png;base64,{map_img}">'

    html += """
        <div class="page-break"></div>
        <h2>Earthquakes</h2>
    """
    if not quakes_df.empty:
        table_html = quakes_df.head(10)[['time', 'magnitude', 'distance_km', 'place']].to_html(index=False)
        html += table_html

    html += """
        <div class="page-break"></div>
        <h2>Weather Forecast</h2>
    """
    if not forecast_df.empty:
        table_html = forecast_df[['name', 'temperature', 'shortForecast']].to_html(index=False)
        html += table_html

    html += """
        <div class="page-break"></div>
        <h2>Alerts</h2>
    """
    if not alerts_df.empty:
        table_html = alerts_df[['event', 'severity', 'areaDesc']].to_html(index=False)
        html += table_html
    else:
        html += "<p>No active alerts.</p>"

    html += "</body></html>"
    return html

# === MAIN APP ===
def main():
    st.title("🌍 Location-Based Disaster Report Generator")
    st.markdown("Real-time earthquake, weather, and alert analysis with PDF export.")

    # === SIDEBAR INPUTS ===
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        input_method = st.radio("Location Input", ["Coordinates", "City Name"])
        
        if input_method == "Coordinates":
            lat = st.number_input("Latitude", value=37.7749, format="%.6f")
            lon = st.number_input("Longitude", value=-122.4194, format="%.6f")
            location_name = f"Custom Location ({lat:.4f}, {lon:.4f})"
        else:
            city = st.text_input("City Name", "San Francisco")
            if st.button("Geocode"):
                with st.spinner("Geocoding..."):
                    lat, lon = geocode_location(city)
                    if lat:
                        st.success(f"Found: {lat:.4f}, {lon:.4f}")
                        location_name = city
                    else:
                        st.error("City not found.")
                        lat, lon = 37.7749, -122.4194
                        location_name = "San Francisco"
            else:
                lat, lon = 37.7749, -122.4194
                location_name = "San Francisco"

        country = st.selectbox("Country", ["US", "CA", "MX"], index=0)
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now())

        st.header("🎨 Theme")
        primary_color = st.color_picker("Primary Color", "#FF6B6B")
        secondary_color = st.color_picker("Secondary Color", "#4ECDC4")
        background_color = st.color_picker("Background", "#FFFFFF")

        inject_custom_css(primary_color, secondary_color, background_color)

    # Store in session state
    st.session_state.update({
        "lat": lat, "lon": lon, "location_name": location_name,
        "start_date": start_date, "end_date": end_date,
        "country": country, "primary_color": primary_color, "secondary_color": secondary_color
    })

    # === MAP PREVIEW ===
    st.subheader("📍 Location Preview")
    preview_map = folium.Map(location=[lat, lon], zoom_start=9)
    folium.Marker([lat, lon], popup=location_name).add_to(preview_map)
    folium_static(preview_map, width=700, height=300)

    # === DATA FETCHING ===
    with st.spinner("Fetching earthquake data..."):
        quakes_df = fetch_earthquakes(lat, lon, start_date, end_date)
    
    with st.spinner("Fetching weather data..."):
        forecast_url, _ = get_weather_grid(lat, lon)
        forecast_df = fetch_forecast(forecast_url)
    
    with st.spinner("Fetching alerts..."):
        alerts_df = fetch_alerts(lat, lon, country)

    # === TABS ===
    tab1, tab2, tab3, tab4 = st.tabs(["Executive Summary", "Earthquakes", "Weather", "Alerts"])

    # === TAB 1: Executive Summary ===
    with tab1:
        st.header(f"Report for {location_name}")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Earthquakes", len(quakes_df))
        with col2:
            st.metric("Active Alerts", len(alerts_df))
        with col3:
            avg_temp = forecast_df["temperature"].head(6).mean() if not forecast_df.empty else 0
            st.metric("Avg Temp (3 days)", f"{avg_temp:.1f}°F")
        with col4:
            risk = "High" if len(quakes_df) > 5 or len(alerts_df) > 0 else "Low"
            st.metric("Risk Level", risk)

        col1, col2 = st.columns(2)
        with col1:
            if not quakes_df.empty:
                bins = [0, 10, 100, 500, 1000]
                labels = ["0-10km", "11-100km", "101-500km", ">500km"]
                quakes_df['bin'] = pd.cut(quakes_df['distance_km'], bins=bins, labels=labels)
                fig = px.pie(values=quakes_df['bin'].value_counts(), names=labels, title="Quakes by Distance")
                fig.update_traces(marker=dict(colors=[primary_color, secondary_color]))
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if not forecast_df.empty:
                daily = forecast_df[::2].head(7)
                fig = px.line(daily, x="name", y="temperature", title="7-Day Temperature")
                fig.update_traces(line_color=secondary_color)
                st.plotly_chart(fig, use_container_width=True)

        m = create_folium_map(lat, lon, quakes_df, alerts_df)
        st.components.v1.html(m._repr_html_(), height=500)

    # === TAB 2: Earthquakes ===
    with tab2:
        if quakes_df.empty:
            st.info("No earthquakes found in the selected range.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Strongest", f"M{quakes_df['magnitude'].max():.1f}")
            with col2:
                st.metric("Avg Depth", f"{quakes_df['depth'].mean():.1f} km")
            with col3:
                st.metric("Within 100km", len(quakes_df[quakes_df['distance_km'] <= 100]))

            col1, col2 = st.columns(2)
            with col1:
                fig = px.scatter(quakes_df, x="time", y="magnitude", size="distance_km", title="Magnitude Over Time")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.histogram(quakes_df, x="magnitude", nbins=20, title="Magnitude Distribution")
                fig.update_traces(marker_color=primary_color)
                st.plotly_chart(fig, use_container_width=True)

            m = create_folium_map(lat, lon, quakes_df)
            folium_static(m, width=700, height=400)

            display_df = quakes_df[['time', 'magnitude', 'distance_km', 'place']].copy()
            display_df['time'] = display_df['time'].dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(display_df.head(20), use_container_width=True)

    # === TAB 3: Weather ===
    with tab3:
        if forecast_df.empty:
            st.info("Weather data unavailable for this location (NOAA is US-only).")
        else:
            current = forecast_df.iloc[0]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current", f"{current['temperature']}°F")
            with col2:
                st.metric("Wind", current['windSpeed'])
            with col3:
                st.metric("Precip", f"{current['probabilityOfPrecipitation']}%")

            fig = go.Figure()
            daily = forecast_df[::2].head(7)
            fig.add_trace(go.Scatter(x=daily["name"], y=daily["temperature"], mode="lines+markers", name="Temp"))
            fig.update_layout(title="7-Day Forecast")
            st.plotly_chart(fig, use_container_width=True)

            table_df = forecast_df[['name', 'temperature', 'shortForecast', 'windSpeed', 'probabilityOfPrecipitation']].copy()
            table_df.rename(columns={"name": "Day", "temperature": "Temp (°F)", "shortForecast": "Conditions", "windSpeed": "Wind", "probabilityOfPrecipitation": "Precip %"}, inplace=True)
            st.dataframe(table_df, use_container_width=True)

    # === TAB 4: Alerts ===
    with tab4:
        if alerts_df.empty:
            st.success("No active alerts.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Alerts", len(alerts_df))
            with col2:
                severe = len(alerts_df[alerts_df['severity'] == 'Severe'])
                st.metric("Severe", severe)

            fig = px.pie(alerts_df, names="event", title="Alerts by Type")
            st.plotly_chart(fig, use_container_width=True)

            for _, alert in alerts_df.iterrows():
                with st.expander(f"⚠️ {alert['event']} - {alert['severity']}"):
                    st.write(f"**Area:** {alert['areaDesc']}")
                    st.write(f"**Effective:** {alert['effective']}")
                    st.write(f"**Expires:** {alert['expires']}")
                    st.write(alert['description'])

    # === PDF EXPORT ===
    if st.button("📄 Generate and Download PDF Report", type="primary"):
        with st.spinner("Generating PDF..."):
            try:
                html_content = generate_pdf_html(
                    "Disaster Report", location_name, quakes_df, forecast_df, alerts_df,
                    primary_color, secondary_color
                )
                pdf_bytes = HTML(string=html_content).write_pdf()
                
                st.download_button(
                    label="Download PDF Now",
                    data=pdf_bytes,
                    file_name=f"{location_name.replace(' ', '_')}_Report_2025-10-25.pdf",
                    mime="application/pdf"
                )
                st.success("PDF ready for download!")
            except Exception as e:
                st.error(f"PDF generation failed: {str(e)}")

if __name__ == "__main__":
    main()
