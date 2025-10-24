import streamlit as st
import re
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
import time

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="PanditaData Disaster Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
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
        font-weight: bold;
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
    .metric-card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        margin: 5px 0;
    }
    .stDataFrame {
        background-color: #1e1e1e;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def geocode_location(query):
    """Convert location query to coordinates"""
    try:
        geolocator = Nominatim(user_agent="panditadata_disaster_v1")
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

def fetch_earthquakes(lat, lon, radius_km=500, days=30, min_mag=2.5):
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
        'limit': 1000
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
        
        # Calculate distance from user
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
            'distance_km': round(distance_km, 1),
            'significance': props.get('sig', 0),
            'tsunami': props.get('tsunami', 0) == 1
        }
        earthquakes.append(earthquake)
    
    df = pd.DataFrame(earthquakes)
    if not df.empty:
        df = df.sort_values('time', ascending=False)
    return df

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

def fetch_weather_forecast(lat, lon):
    """Get weather forecast from Open-Meteo"""
    params = {
        'latitude': lat,
        'longitude': lon,
        'current_weather': 'true',
        'timezone': 'auto',
        'forecast_days': 3
    }
    
    try:
        response = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching weather data: {e}")
        return None

def fetch_weather_alerts(lat, lon):
    """Fetch weather alerts from NWS (US only)"""
    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        points_response = requests.get(points_url, headers={'User-Agent': 'PanditaDataApp'}, timeout=30)
        
        if points_response.status_code == 200:
            points_data = points_response.json()
            alerts_url = points_data['properties']['forecastOffice'] + '/alerts'
            alerts_response = requests.get(alerts_url, headers={'User-Agent': 'PanditaDataApp'}, timeout=30)
            
            if alerts_response.status_code == 200:
                return alerts_response.json()
    except Exception:
        pass  # Silent fail for non-US locations
    return None

def fetch_space_weather():
    """Get space weather data"""
    try:
        kp_response = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=30)
        kp_data = kp_response.json() if kp_response.status_code == 200 else []
        
        return {
            'kp_index': kp_data[-1][1] if kp_data else 'N/A',
            'timestamp': datetime.now()
        }
    except Exception as e:
        st.error(f"Error fetching space weather: {e}")
        return None

def fetch_hurricanes():
    """Get active hurricane information"""
    try:
        response = requests.get("https://www.nhc.noaa.gov/products.json", timeout=30)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error fetching hurricane data: {e}")
    return None

def create_pdf_report(location_data, earthquake_data, weather_data, space_weather, alerts):
    """Generate comprehensive PDF report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
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
    
    critical_count = len([eq for _, eq in earthquake_data.iterrows() 
                         if classify_earthquake_risk(eq['magnitude'], eq['distance_km']) in ['CATASTROPHIC', 'CRITICAL']])
    
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
        eq_table_data = [['Time', 'Magnitude', 'Distance', 'Location', 'Risk']]
        for _, eq in earthquake_data.head(15).iterrows():
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
    story.append(Paragraph("WEATHER CONDITIONS", styles['Heading2']))
    if weather_data and 'current_weather' in weather_data:
        current = weather_data['current_weather']
        story.append(Paragraph(f"Current Temperature: {current['temperature']}°C", styles['Normal']))
        story.append(Paragraph(f"Wind Speed: {current['windspeed']} km/h", styles['Normal']))
    
    # Space Weather
    story.append(Paragraph("SPACE WEATHER", styles['Heading2']))
    if space_weather:
        story.append(Paragraph(f"Geomagnetic Kp Index: {space_weather['kp_index']}", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def create_magnitude_chart(df):
    """Create magnitude distribution using Streamlit native chart"""
    if df.empty:
        return
    
    # Magnitude distribution
    mag_bins = [2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 10.0]
    mag_labels = ['2.5-3.0', '3.0-4.0', '4.0-5.0', '5.0-6.0', '6.0-7.0', '7.0+']
    
    df['mag_bin'] = pd.cut(df['magnitude'], bins=mag_bins, labels=mag_labels, right=False)
    mag_counts = df['mag_bin'].value_counts().sort_index()
    
    chart_data = pd.DataFrame({
        'Magnitude Range': mag_counts.index,
        'Count': mag_counts.values
    })
    
    st.subheader("📊 Magnitude Distribution")
    st.bar_chart(chart_data.set_index('Magnitude Range'))

def create_time_series_chart(df):
    """Create time series chart of earthquakes using Streamlit"""
    if df.empty:
        return
    
    # Group by day
    df_daily = df.copy()
    df_daily['date'] = df_daily['time'].dt.date
    daily_counts = df_daily.groupby('date').size().reset_index(name='count')
    daily_counts = daily_counts.sort_values('date')
    
    st.subheader("📈 Daily Earthquake Frequency")
    st.line_chart(daily_counts.set_index('date'))

def create_depth_chart(df):
    """Create depth distribution chart"""
    if df.empty:
        return
    
    st.subheader("🌋 Earthquake Depth Distribution")
    
    # Create depth bins
    depth_bins = [0, 10, 30, 70, 150, 300, 700]
    depth_labels = ['0-10km', '10-30km', '30-70km', '70-150km', '150-300km', '300km+']
    
    df['depth_bin'] = pd.cut(df['depth_km'], bins=depth_bins, labels=depth_labels, right=False)
    depth_counts = df['depth_bin'].value_counts().sort_index()
    
    depth_data = pd.DataFrame({
        'Depth Range': depth_counts.index,
        'Count': depth_counts.values
    })
    
    st.bar_chart(depth_data.set_index('Depth Range'))

# ============================================================================
# STREAMLIT UI
# ============================================================================

def main():
    st.title("🌍 PanditaData Disaster Intelligence Platform")
    st.markdown("### Professional Disaster Monitoring & Space Weather Reporting")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🌍 Location Setup")
        input_method = st.radio("Input Method:", ["City/Address", "Coordinates"])
        
        location_data = None
        
        if input_method == "City/Address":
            location_query = st.text_input("Enter location:", "San Francisco, CA")
            if st.button("📍 Geocode Location"):
                with st.spinner("Finding location..."):
                    location_data = geocode_location(location_query)
                    if location_data['success']:
                        st.success(f"Found: {location_data['address']}")
                        st.session_state['location'] = location_data
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
            st.session_state['location'] = location_data
        
        if 'location' in st.session_state and st.session_state['location']['success']:
            st.markdown("---")
            st.subheader("⚙️ Monitoring Parameters")
            radius_km = st.slider("Search Radius (km)", 50, 1000, 500)
            days_back = st.slider("Days to Analyze", 1, 90, 30)
            min_magnitude = st.slider("Minimum Magnitude", 2.5, 7.0, 4.0)
            
            st.session_state['params'] = {
                'radius_km': radius_km,
                'days_back': days_back,
                'min_magnitude': min_magnitude
            }
        
        st.markdown("---")
        if st.button("🔄 Refresh All Data"):
            st.rerun()
    
    # Main content
    if 'location' not in st.session_state or not st.session_state['location']['success']:
        st.info("👈 Please configure your location in the sidebar to begin monitoring.")
        return
    
    location = st.session_state['location']
    params = st.session_state.get('params', {'radius_km': 500, 'days_back': 30, 'min_magnitude': 4.0})
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌋 Earthquake Monitor", 
        "🌤️ Weather & Alerts", 
        "🛰️ Space Weather", 
        "🌀 Hurricane Tracker",
        "📊 Full Report"
    ])
    
    with tab1:
        st.header("Earthquake Monitoring")
        
        with st.spinner("Fetching earthquake data from USGS..."):
            eq_data = fetch_earthquakes(
                location['latitude'], 
                location['longitude'], 
                params['radius_km'], 
                params['days_back'], 
                params['min_magnitude']
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
                        st.subheader("🚨 High Priority Alerts")
                        for eq, risk in critical_quakes[:3]:
                            alert_class = "critical-alert" if risk == 'CATASTROPHIC' else "high-alert"
                            st.markdown(f"""
                            <div class="{alert_class}">
                                <strong>{risk} ALERT</strong><br>
                                M{eq['magnitude']:.1f} earthquake {eq['distance_km']:.0f}km away<br>
                                {eq['location']}<br>
                                Time: {eq['time'].strftime('%Y-%m-%d %H:%M UTC')}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Charts using Streamlit native functions
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        create_magnitude_chart(df_earthquakes)
                    
                    with col2:
                        create_time_series_chart(df_earthquakes)
                    
                    create_depth_chart(df_earthquakes)
                    
                    # Map
                    st.subheader("Interactive Earthquake Map")
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
                    
                    # Add search radius circle
                    folium.Circle(
                        map_center,
                        radius=params['radius_km'] * 1000,  # Convert to meters
                        color='blue',
                        fill=True,
                        fillOpacity=0.1,
                        popup=f"Search Radius: {params['radius_km']}km"
                    ).add_to(m)
                    
                    folium_static(m, width=800, height=500)
                    
                    # Data table
                    st.subheader("Recent Earthquakes")
                    display_df = df_earthquakes[['time', 'magnitude', 'distance_km', 'location', 'depth_km']].copy()
                    display_df['time'] = display_df['time'].dt.strftime('%Y-%m-%d %H:%M')
                    display_df['distance_km'] = display_df['distance_km'].round(1)
                    st.dataframe(display_df.head(20), use_container_width=True)
                    
                else:
                    st.success("✅ No earthquakes detected in the selected area and time period.")
            else:
                st.error("❌ Failed to fetch earthquake data from USGS")
    
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
                        st.metric("Wind Direction", f"{current['winddirection']}°")
                    with col4:
                        st.metric("Weather Code", current['weathercode'])
                
                # Weather alerts
                alerts_data = fetch_weather_alerts(location['latitude'], location['longitude'])
                if alerts_data and 'features' in alerts_data and alerts_data['features']:
                    st.subheader("⚠️ Weather Alerts")
                    for alert in alerts_data['features'][:5]:
                        props = alert['properties']
                        st.warning(f"**{props['event']}**: {props['headline']}")
                else:
                    st.info("No active weather alerts for this location")
            else:
                st.error("Failed to fetch weather data")
    
    with tab3:
        st.header("Space Weather")
        
        with st.spinner("Fetching space weather data..."):
            space_data = fetch_space_weather()
            
            if space_data:
                col1, col2, col3 = st.columns(3)
                with col1:
                    kp_value = space_data['kp_index']
                    st.metric("Geomagnetic Kp Index", kp_value)
                with col2:
                    if kp_value != 'N/A':
                        kp_num = float(kp_value)
                        if kp_num >= 5:
                            st.error("🌩️ Geomagnetic Storm Active")
                        elif kp_num >= 4:
                            st.warning("🌤️ Unsettled Geomagnetic Conditions")
                        else:
                            st.success("☀️ Quiet Geomagnetic Conditions")
                with col3:
                    st.metric("Last Updated", space_data['timestamp'].strftime('%H:%M UTC'))
                
                st.info("""
                **Kp Index Guide:**
                - 0-4: Quiet to unsettled conditions
                - 5: Minor geomagnetic storm
                - 6: Moderate geomagnetic storm  
                - 7-9: Strong to severe geomagnetic storm
                """)
            else:
                st.error("Failed to fetch space weather data")
    
    with tab4:
        st.header("Hurricane & Tropical Storm Tracking")
        
        with st.spinner("Checking for active storms..."):
            hurricanes = fetch_hurricanes()
            
            if hurricanes and 'products' in hurricanes:
                active_storms = []
                for product in hurricanes['products']:
                    if 'tropical' in product.get('name', '').lower():
                        active_storms.append(product)
                
                if active_storms:
                    st.subheader("🌀 Active Tropical Systems")
                    for storm in active_storms[:5]:
                        with st.expander(f"🌪️ {storm.get('name', 'Unknown Storm')}"):
                            st.write(f"**Type**: {storm.get('name', 'N/A')}")
                            st.write(f"**Issued**: {storm.get('issuanceTime', 'N/A')}")
                else:
                    st.success("✅ No active tropical storms reported")
            else:
                st.info("No hurricane data available or no active storms")
    
    with tab5:
        st.header("Comprehensive PDF Report")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            ### 📄 Professional Report Generation
            
            Generate a comprehensive PDF report containing:
            - Location overview and coordinates
            - Earthquake activity and risk assessment
            - Weather conditions and alerts
            - Space weather status
            - Executive summary
            
            This report is suitable for emergency planning, research documentation, 
            and professional disaster management purposes.
            """)
        
        with col2:
            st.image("https://via.placeholder.com/200x200/2E86AB/FFFFFF?text=PDF", width=150)
        
        if st.button("🔄 Generate Full PDF Report", type="primary"):
            with st.spinner("Compiling comprehensive report..."):
                # Fetch all data
                eq_data_raw = fetch_earthquakes(
                    location['latitude'], 
                    location['longitude'], 
                    params['radius_km'], 
                    params['days_back'], 
                    params['min_magnitude']
                )
                df_earthquakes = process_earthquake_data(eq_data_raw, location['latitude'], location['longitude']) if eq_data_raw else pd.DataFrame()
                weather_data = fetch_weather_forecast(location['latitude'], location['longitude'])
                space_data = fetch_space_weather()
                alerts_data = fetch_weather_alerts(location['latitude'], location['longitude'])
                
                pdf_buffer = create_pdf_report(
                    location, 
                    df_earthquakes, 
                    weather_data, 
                    space_data, 
                    alerts_data
                )
                
                # Download button
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_buffer,
                    file_name=f"disaster_intelligence_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
        
        # Quick summary
        st.subheader("📈 Current Situation Summary")
        
        if 'df_earthquakes' in locals() and not df_earthquakes.empty:
            recent_quakes = df_earthquakes[df_earthquakes['time'] > datetime.now() - timedelta(days=7)]
            st.write(f"**Recent seismic activity**: {len(recent_quakes)} earthquakes in past 7 days")
            
            # Risk assessment
            high_risk = len([eq for _, eq in df_earthquakes.iterrows() 
                           if classify_earthquake_risk(eq['magnitude'], eq['distance_km']) in ['CATASTROPHIC', 'CRITICAL']])
            if high_risk > 0:
                st.error(f"🚨 **{high_risk} high-risk earthquakes** detected in monitoring area")
            else:
                st.success("✅ No high-risk seismic activity detected")
        else:
            st.info("No earthquake data available for summary")

if __name__ == "__main__":
    main()
