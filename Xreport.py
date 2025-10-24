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
from reportlab.pdfgen import canvas
import base64
from io import BytesIO

# -------------------------------------------------
# 3. PAGE CONFIG & CSS
# -------------------------------------------------
import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import folium_static
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import base64

# Page configuration
st.set_page_config(
    page_title="PanditaData Disaster Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .critical-alert {
        background-color: #8b0000;
        color: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff0000;
        margin: 10px 0;
    }
    .high-alert {
        background-color: #ff8c00;
        color: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ffa500;
        margin: 10px 0;
    }
    .moderate-alert {
        background-color: #ffd700;
        color: black;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ffff00;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 1. LOCATION SERVICES
# ============================================================================

def geocode_location(query):
    """Convert location query to coordinates using Nominatim (free)"""
    try:
        geolocator = Nominatim(user_agent="panditadata_disaster_monitor")
        location = geolocator.geocode(query, exactly_one=True, timeout=10)
        if location:
            return {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'address': location.address,
                'success': True
            }
    except Exception as e:
        st.error(f"Geocoding error: {e}")
    return {'success': False}

# ============================================================================
# 2. EARTHQUAKE MONITORING (USGS)
# ============================================================================

def fetch_earthquakes(lat, lon, radius_km, days=30, min_mag=2.5):
    """Fetch earthquake data from USGS API"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    params = {
        'format': 'geojson',
        'starttime': start_date.strftime('%Y-%m-%d'),
        'endtime': end_date.strftime('%Y-%m-%d'),
        'latitude': lat,
        'longitude': lon,
        'maxradiuskm': radius_km,
        'minmagnitude': min_mag,
        'orderby': 'time',
        'limit': 2000
    }
    
    try:
        response = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching earthquake data: {e}")
        return None

def process_earthquake_data(geojson, user_lat, user_lon):
    """Process earthquake data into DataFrame"""
    if not geojson or 'features' not in geojson:
        return pd.DataFrame()
    
    earthquakes = []
    for feature in geojson['features']:
        props = feature['properties']
        coords = feature['geometry']['coordinates']
        
        # Calculate distance
        eq_location = (coords[1], coords[0])
        user_location = (user_lat, user_lon)
        distance_km = geodesic(user_location, eq_location).kilometers
        
        earthquake = {
            'id': feature['id'],
            'magnitude': props.get('mag', 0),
            'latitude': coords[1],
            'longitude': coords[0],
            'depth_km': coords[2],
            'location': props.get('place', 'Unknown'),
            'time': datetime.fromtimestamp(props['time']/1000),
            'distance_km': distance_km,
            'significance': props.get('sig', 0),
            'tsunami': props.get('tsunami', 0) == 1
        }
        earthquakes.append(earthquake)
    
    return pd.DataFrame(earthquakes)

def classify_earthquake_risk(magnitude, distance_km, tsunami=False):
    """Classify earthquake risk level"""
    if tsunami and magnitude >= 7.0:
        return 'CATASTROPHIC'
    elif magnitude >= 8.0:
        return 'CATASTROPHIC'
    elif magnitude >= 7.0:
        return 'CRITICAL'
    elif magnitude >= 6.0:
        return 'SEVERE'
    elif magnitude >= 5.0 and distance_km <= 100:
        return 'MODERATE'
    elif magnitude >= 4.0 and distance_km <= 50:
        return 'MINOR'
    else:
        return 'LOW'

# ============================================================================
# 3. WEATHER FORECASTING (Open-Meteo)
# ============================================================================

def fetch_weather_forecast(lat, lon):
    """Get weather forecast from Open-Meteo (free)"""
    params = {
        'latitude': lat,
        'longitude': lon,
        'hourly': 'temperature_2m,precipitation,weather_code,wind_speed_10m',
        'daily': 'weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum',
        'timezone': 'auto',
        'forecast_days': 7
    }
    
    try:
        response = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching weather data: {e}")
        return None

def interpret_weather_code(code):
    """Convert WMO weather code to description"""
    codes = {
        0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
        45: 'Fog', 48: 'Depositing rime fog', 51: 'Light drizzle', 53: 'Moderate drizzle',
        61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain',
        71: 'Slight snow', 73: 'Moderate snow', 75: 'Heavy snow',
        95: 'Thunderstorm', 96: 'Thunderstorm with hail', 99: 'Heavy thunderstorm with hail'
    }
    return codes.get(int(code), 'Unknown')

# ============================================================================
# 4. WEATHER ALERTS (NWS - US only)
# ============================================================================

def fetch_weather_alerts(lat, lon):
    """Fetch weather alerts from NWS (US only)"""
    try:
        # First get grid point
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        points_response = requests.get(points_url, headers={'User-Agent': 'PanditaDataApp'}, timeout=30)
        
        if points_response.status_code == 200:
            points_data = points_response.json()
            alerts_url = points_data['properties']['forecastOffice'] + '/alerts'
            alerts_response = requests.get(alerts_url, headers={'User-Agent': 'PanditaDataApp'}, timeout=30)
            
            if alerts_response.status_code == 200:
                return alerts_response.json()
    except Exception as e:
        st.sidebar.info("Weather alerts only available for US locations")
    return None

# ============================================================================
# 5. SPACE WEATHER (NASA/SWPC)
# ============================================================================

def fetch_space_weather():
    """Get space weather data from NASA/SWPC"""
    try:
        # Geomagnetic storms
        kp_response = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=30)
        kp_data = kp_response.json() if kp_response.status_code == 200 else []
        
        # Solar flares
        flare_response = requests.get("https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json", timeout=30)
        flare_data = flare_response.json() if flare_response.status_code == 200 else []
        
        return {
            'kp_index': kp_data[-1][1] if kp_data else 'N/A',
            'solar_flares': flare_data,
            'timestamp': datetime.now()
        }
    except Exception as e:
        st.error(f"Error fetching space weather: {e}")
        return None

# ============================================================================
# 6. HURRICANE TRACKING (NOAA)
# ============================================================================

def fetch_active_hurricanes():
    """Get active hurricane information from NOAA"""
    try:
        response = requests.get("https://www.nhc.noaa.gov/current.json", timeout=30)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error fetching hurricane data: {e}")
    return None

# ============================================================================
# 7. PDF REPORT GENERATION
# ============================================================================

def create_pdf_report(location_data, earthquake_data, weather_data, space_weather, hurricanes, alerts):
    """Generate comprehensive PDF report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#2E86AB'),
        alignment=1
    )
    story.append(Paragraph("DISASTER INTELLIGENCE REPORT", title_style))
    story.append(Spacer(1, 20))
    
    # Location Information
    story.append(Paragraph(f"Location: {location_data['address']}", styles['Heading2']))
    story.append(Paragraph(f"Coordinates: {location_data['latitude']:.4f}, {location_data['longitude']:.4f}", styles['Normal']))
    story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("EXECUTIVE SUMMARY", styles['Heading2']))
    
    # Count alerts by severity
    critical_count = len([eq for _, eq in earthquake_data.iterrows() if classify_earthquake_risk(eq['magnitude'], eq['distance_km']) in ['CATASTROPHIC', 'CRITICAL']])
    
    summary_text = f"""
    This report covers disaster monitoring for {location_data['address']}. 
    Found {len(earthquake_data)} earthquakes in the area, with {critical_count} requiring immediate attention.
    Current weather conditions and space weather status are included below.
    """
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Earthquake Section
    story.append(Paragraph("EARTHQUAKE ACTIVITY", styles['Heading2']))
    if not earthquake_data.empty:
        # Create simplified table for PDF
        eq_table_data = [['Time', 'Magnitude', 'Distance', 'Location', 'Risk']]
        for _, eq in earthquake_data.head(10).iterrows():
            risk = classify_earthquake_risk(eq['magnitude'], eq['distance_km'])
            eq_table_data.append([
                eq['time'].strftime('%m/%d %H:%M'),
                f"{eq['magnitude']:.1f}",
                f"{eq['distance_km']:.0f} km",
                eq['location'][:30] + '...' if len(eq['location']) > 30 else eq['location'],
                risk
            ])
        
        eq_table = Table(eq_table_data, colWidths=[1*inch, 0.7*inch, 0.8*inch, 2*inch, 1*inch])
        eq_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(eq_table)
    else:
        story.append(Paragraph("No significant earthquake activity detected.", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Weather Section
    story.append(Paragraph("WEATHER FORECAST", styles['Heading2']))
    if weather_data:
        current_temp = weather_data['hourly']['temperature_2m'][0] if 'hourly' in weather_data else 'N/A'
        story.append(Paragraph(f"Current Temperature: {current_temp}°C", styles['Normal']))
    
    # Space Weather
    story.append(Paragraph("SPACE WEATHER", styles['Heading2']))
    if space_weather:
        story.append(Paragraph(f"Geomagnetic Kp Index: {space_weather['kp_index']}", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ============================================================================
# 8. STREAMLIT UI
# ============================================================================

def main():
    st.title("🌍 PanditaData Disaster Intelligence Platform")
    st.markdown("### Professional Disaster Monitoring & Space Weather Reporting")
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x50/2E86AB/FFFFFF?text=PanditaData", width=200)
        st.markdown("---")
        
        # Location input
        st.subheader("📍 Location Setup")
        input_method = st.radio("Input Method:", ["City/Address", "Coordinates"])
        
        location_data = None
        
        if input_method == "City/Address":
            location_query = st.text_input("Enter location:", "San Francisco, CA")
            if st.button("Geocode Location"):
                with st.spinner("Finding location..."):
                    location_data = geocode_location(location_query)
                    if location_data['success']:
                        st.success(f"Found: {location_data['address']}")
                    else:
                        st.error("Location not found")
        else:
            col1, col2 = st.columns(2)
            with col1:
                lat = st.number_input("Latitude", value=37.7749, format="%.6f")
            with col2:
                lon = st.number_input("Longitude", value=-122.4194, format="%.6f")
            location_data = {
                'latitude': lat,
                'longitude': lon,
                'address': f"Custom Location ({lat:.4f}, {lon:.4f})",
                'success': True
            }
        
        if location_data and location_data['success']:
            st.session_state['location'] = location_data
        
        st.markdown("---")
        st.subheader("⚙️ Monitoring Parameters")
        radius_km = st.slider("Search Radius (km)", 50, 1000, 500)
        days_back = st.slider("Days to Analyze", 1, 90, 30)
        min_magnitude = st.slider("Minimum Magnitude", 2.5, 7.0, 4.0)
        
        st.markdown("---")
        if st.button("🔄 Refresh All Data"):
            st.rerun()
    
    # Main content
    if 'location' not in st.session_state or not st.session_state['location']['success']:
        st.info("👈 Please configure your location in the sidebar to begin monitoring.")
        return
    
    location = st.session_state['location']
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌋 Earthquake Monitor", 
        "🌤️ Weather & Alerts", 
        "🛰️ Space Weather", 
        "🌀 Hurricane Tracker",
        "📊 Full Report"
    ])
    
    with tab1:
        st.header("Earthquake Monitoring")
        
        with st.spinner("Fetching earthquake data..."):
            eq_data = fetch_earthquakes(
                location['latitude'], 
                location['longitude'], 
                radius_km, 
                days_back, 
                min_magnitude
            )
            
            if eq_data:
                df_earthquakes = process_earthquake_data(eq_data, location['latitude'], location['longitude'])
                
                if not df_earthquakes.empty:
                    # Statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Earthquakes", len(df_earthquakes))
                    with col2:
                        st.metric("Largest Magnitude", f"{df_earthquakes['magnitude'].max():.1f}")
                    with col3:
                        st.metric("Nearest (km)", f"{df_earthquakes['distance_km'].min():.0f}")
                    with col4:
                        tsunami_count = df_earthquakes['tsunami'].sum()
                        st.metric("Tsunami Warnings", tsunami_count)
                    
                    # Risk alerts
                    critical_quakes = []
                    for _, eq in df_earthquakes.iterrows():
                        risk = classify_earthquake_risk(eq['magnitude'], eq['distance_km'], eq['tsunami'])
                        if risk in ['CATASTROPHIC', 'CRITICAL']:
                            critical_quakes.append((eq, risk))
                    
                    if critical_quakes:
                        for eq, risk in critical_quakes[:3]:  # Show top 3
                            alert_class = "critical-alert" if risk == 'CATASTROPHIC' else "high-alert"
                            st.markdown(f"""
                            <div class="{alert_class}">
                                <strong>{risk} ALERT</strong><br>
                                M{eq['magnitude']:.1f} earthquake {eq['distance_km']:.0f}km away<br>
                                {eq['location']}<br>
                                Time: {eq['time'].strftime('%Y-%m-%d %H:%M UTC')}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    
                    st.subheader("Earthquake Map")
                    map_center = [location['latitude'], location['longitude']]
                    m = folium.Map(location=map_center, zoom_start=6)
                    
                    # Add user location
                    folium.Marker(
                        map_center,
                        popup="Your Location",
                        tooltip="You are here",
                        icon=folium.Icon(color='blue', icon='star')
                    ).add_to(m)
                    
                    # Add earthquakes
                    for _, eq in df_earthquakes.iterrows():
                        risk = classify_earthquake_risk(eq['magnitude'], eq['distance_km'])
                        color = 'red' if risk in ['CATASTROPHIC', 'CRITICAL'] else 'orange' if risk == 'SEVERE' else 'yellow'
                        
                        folium.CircleMarker(
                            [eq['latitude'], eq['longitude']],
                            radius=eq['magnitude'] * 2,
                            popup=f"M{eq['magnitude']:.1f} - {eq['location']}",
                            tooltip=f"M{eq['magnitude']:.1f} - {eq['distance_km']:.0f}km",
                            color=color,
                            fillColor=color,
                            fillOpacity=0.6
                        ).add_to(m)
                    
                    folium_static(m, width=800, height=500)
                    
                    # Data table
                    st.subheader("Recent Earthquakes")
                    display_df = df_earthquakes[['time', 'magnitude', 'distance_km', 'location', 'depth_km']].copy()
                    display_df['time'] = display_df['time'].dt.strftime('%Y-%m-%d %H:%M')
                    display_df['distance_km'] = display_df['distance_km'].round(1)
                    st.dataframe(display_df.head(20), use_container_width=True)
                    
                else:
                    st.success("No earthquakes detected in the selected area and time period.")
            else:
                st.error("Failed to fetch earthquake data")
    
    with tab2:
        st.header("Weather Monitoring")
        
        with st.spinner("Fetching weather data..."):
            weather_data = fetch_weather_forecast(location['latitude'], location['longitude'])
            
            if weather_data:
                # Current weather
                if 'current_weather' in weather_data:
                    current = weather_data['current_weather']
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Temperature", f"{current['temperature']}°C")
                    with col2:
                        st.metric("Wind Speed", f"{current['windspeed']} km/h")
                    with col3:
                        weather_desc = interpret_weather_code(current['weathercode'])
                        st.metric("Conditions", weather_desc)
                
                # Weather alerts
                alerts_data = fetch_weather_alerts(location['latitude'], location['longitude'])
                if alerts_data and 'features' in alerts_data:
                    st.subheader("Weather Alerts")
                    for alert in alerts_data['features'][:5]:
                        props = alert['properties']
                        st.warning(f"**{props['event']}**: {props['headline']}")
    
    with tab3:
        st.header("Space Weather")
        
        with st.spinner("Fetching space weather data..."):
            space_data = fetch_space_weather()
            
            if space_data:
                col1, col2, col3 = st.columns(3)
                with col1:
                    kp_value = float(space_data['kp_index']) if space_data['kp_index'] != 'N/A' else 0
                    st.metric("Geomagnetic Kp Index", space_data['kp_index'])
                with col2:
                    if kp_value >= 5:
                        st.error("Geomagnetic Storm Active")
                    elif kp_value >= 4:
                        st.warning("Unsettled Geomagnetic Conditions")
                    else:
                        st.success("Quiet Geomagnetic Conditions")
    
    with tab4:
        st.header("Hurricane & Tropical Storm Tracking")
        
        with st.spinner("Checking for active storms..."):
            hurricanes = fetch_active_hurricanes()
            
            if hurricanes:
                for storm in hurricanes.get('activeStorms', [])[:5]:
                    with st.expander(f"🌀 {storm.get('name', 'Unknown')} - {storm.get('basin', 'Unknown')}"):
                        st.write(f"**Location**: {storm.get('location', 'N/A')}")
                        st.write(f"**Intensity**: {storm.get('intensity', 'N/A')}")
                        st.write(f"**Movement**: {storm.get('movement', 'N/A')}")
            else:
                st.info("No active tropical storms reported")
    
    with tab5:
        st.header("Comprehensive PDF Report")
        
        # Generate PDF
        if st.button("📄 Generate Professional PDF Report"):
            with st.spinner("Generating comprehensive report..."):
                # Fetch all data
                eq_data_raw = fetch_earthquakes(location['latitude'], location['longitude'], radius_km, days_back, min_magnitude)
                df_earthquakes = process_earthquake_data(eq_data_raw, location['latitude'], location['longitude']) if eq_data_raw else pd.DataFrame()
                weather_data = fetch_weather_forecast(location['latitude'], location['longitude'])
                space_data = fetch_space_weather()
                hurricane_data = fetch_active_hurricanes()
                alerts_data = fetch_weather_alerts(location['latitude'], location['longitude'])
                
                pdf_buffer = create_pdf_report(
                    location, 
                    df_earthquakes, 
                    weather_data, 
                    space_data, 
                    hurricane_data, 
                    alerts_data
                )
                
                # Download button
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_buffer,
                    file_name=f"disaster_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )
        
        # Quick summary
        st.subheader("Current Situation Summary")
        
        # Earthquake summary
        if 'df_earthquakes' in locals() and not df_earthquakes.empty:
            recent_quakes = df_earthquakes[df_earthquakes['time'] > datetime.now() - timedelta(days=7)]
            st.write(f"**Recent seismic activity**: {len(recent_quakes)} earthquakes in past 7 days")
            
            # Risk assessment
            high_risk = len([eq for _, eq in df_earthquakes.iterrows() 
                           if classify_earthquake_risk(eq['magnitude'], eq['distance_km']) in ['CATASTROPHIC', 'CRITICAL']])
            if high_risk > 0:
                st.error(f"**{high_risk} high-risk earthquakes** detected in monitoring area")
            else:
                st.success("No high-risk seismic activity detected")

if __name__ == "__main__":
    main()
