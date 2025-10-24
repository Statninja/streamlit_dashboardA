import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import math

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
    .metric-card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Predefined cities
MAJOR_CITIES = {
    "San Francisco, CA": (37.7749, -122.4194),
    "New York, NY": (40.7128, -74.0060),
    "Los Angeles, CA": (34.0522, -118.2437),
    "Chicago, IL": (41.8781, -87.6298),
    "Houston, TX": (29.7604, -95.3698),
    "Miami, FL": (25.7617, -80.1918),
    "Tokyo, Japan": (35.6762, 139.6503),
    "London, UK": (51.5074, -0.1278),
    "Sydney, Australia": (-33.8688, 151.2093)
}

# Core functions
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates using Haversine formula"""
    R = 6371  # Earth radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon/2) * math.sin(delta_lon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

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
        
        # Calculate distance from user using Haversine
        distance_km = calculate_distance(user_lat, user_lon, coords[1], coords[0])
        
        earthquake = {
            'magnitude': props.get('mag', 0),
            'latitude': coords[1],
            'longitude': coords[0],
            'depth_km': coords[2],
            'location': props.get('place', 'Unknown'),
            'time': datetime.fromtimestamp(props['time']/1000),
            'distance_km': round(distance_km, 1),
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

def create_simple_report(location_data, earthquake_data, weather_data, space_weather):
    """Create a simple text report"""
    report = f"""
# DISASTER INTELLIGENCE REPORT

**Location:** {location_data['address']}  
**Coordinates:** {location_data['latitude']:.4f}, {location_data['longitude']:.4f}  
**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}  

## EXECUTIVE SUMMARY

This report covers disaster monitoring for {location_data['address']}. 
Found {len(earthquake_data)} earthquakes in the area.
Current weather conditions and space weather status are included below.

## EARTHQUAKE ACTIVITY
"""
    
    if not earthquake_data.empty:
        report += "\nRecent Earthquakes:\n"
        for _, eq in earthquake_data.head(10).iterrows():
            risk = classify_earthquake_risk(eq['magnitude'], eq['distance_km'])
            report += f"- M{eq['magnitude']:.1f} | {eq['distance_km']:.0f}km | {eq['location']} | {risk}\n"
    else:
        report += "No significant earthquake activity detected.\n"
    
    if weather_data and 'current_weather' in weather_data:
        current = weather_data['current_weather']
        report += f"\n## WEATHER CONDITIONS\n"
        report += f"Temperature: {current['temperature']}°C\n"
        report += f"Wind Speed: {current['windspeed']} km/h\n"
    
    if space_weather:
        report += f"\n## SPACE WEATHER\n"
        report += f"Geomagnetic Kp Index: {space_weather['kp_index']}\n"
    
    return report

# Page navigation
def executive_summary():
    st.title("🌍 Executive Summary")
    
    if 'location' not in st.session_state:
        st.info("Please set your location in the Setup page first.")
        return
        
    location = st.session_state['location']
    params = st.session_state.get('params', {'radius_km': 500, 'days_back': 30, 'min_magnitude': 4.0})
    
    # Fetch all data for summary
    with st.spinner("Loading current disaster intelligence..."):
        # Earthquake data
        eq_data = fetch_earthquakes(
            location['latitude'], 
            location['longitude'], 
            params['radius_km'], 
            7,  # Last 7 days for summary
            params['min_magnitude']
        )
        
        df_earthquakes = process_earthquake_data(eq_data, location['latitude'], location['longitude']) if eq_data else pd.DataFrame()
        
        # Weather data
        weather_data = fetch_weather_forecast(location['latitude'], location['longitude'])
        
        # Space weather
        space_data = fetch_space_weather()
    
    # Summary metrics
    st.subheader("📊 Quick Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if not df_earthquakes.empty:
            st.metric("Recent Earthquakes", len(df_earthquakes))
        else:
            st.metric("Recent Earthquakes", 0)
    
    with col2:
        if not df_earthquakes.empty:
            high_risk = len([eq for _, eq in df_earthquakes.iterrows() 
                           if classify_earthquake_risk(eq['magnitude'], eq['distance_km']) in ['CATASTROPHIC', 'CRITICAL']])
            st.metric("High Risk Events", high_risk)
        else:
            st.metric("High Risk Events", 0)
    
    with col3:
        if weather_data and 'current_weather' in weather_data:
            st.metric("Temperature", f"{weather_data['current_weather']['temperature']}°C")
        else:
            st.metric("Temperature", "N/A")
    
    with col4:
        if space_data:
            st.metric("Space Weather Kp", space_data['kp_index'])
        else:
            st.metric("Space Weather Kp", "N/A")
    
    # Risk alerts
    if not df_earthquakes.empty:
        critical_quakes = []
        for _, eq in df_earthquakes.iterrows():
            risk = classify_earthquake_risk(eq['magnitude'], eq['distance_km'], eq['tsunami'])
            if risk in ['CATASTROPHIC', 'CRITICAL']:
                critical_quakes.append((eq, risk))
        
        if critical_quakes:
            st.subheader("🚨 Critical Alerts")
            for eq, risk in critical_quakes[:3]:
                if risk == 'CATASTROPHIC':
                    st.error(f"**{risk} ALERT**: M{eq['magnitude']:.1f} earthquake {eq['distance_km']:.0f}km away at {eq['location']}")
                else:
                    st.warning(f"**{risk} ALERT**: M{eq['magnitude']:.1f} earthquake {eq['distance_km']:.0f}km away at {eq['location']}")
    
    # Recent activity chart
    if not df_earthquakes.empty:
        st.subheader("📈 Recent Seismic Activity")
        
        # Create time series data
        df_daily = df_earthquakes.copy()
        df_daily['date'] = df_daily['time'].dt.date
        daily_counts = df_daily.groupby('date').size().reset_index(name='count')
        daily_counts = daily_counts.sort_values('date')
        
        # Display as bar chart
        if len(daily_counts) > 1:
            st.bar_chart(daily_counts.set_index('date'))
        else:
            st.info("Not enough data for chart display")
    
    # Weather status
    if weather_data and 'current_weather' in weather_data:
        st.subheader("🌤️ Current Weather")
        current = weather_data['current_weather']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Temperature", f"{current['temperature']}°C")
        with col2:
            st.metric("Wind Speed", f"{current['windspeed']} km/h")
        with col3:
            st.metric("Wind Direction", f"{current['winddirection']}°")

def earthquake_monitor():
    st.title("🌋 Earthquake Monitor")
    
    if 'location' not in st.session_state:
        st.info("Please set your location in the Setup page first.")
        return
        
    location = st.session_state['location']
    params = st.session_state.get('params', {'radius_km': 500, 'days_back': 30, 'min_magnitude': 4.0})
    
    with st.spinner("Fetching earthquake data..."):
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
                
                # Magnitude distribution
                st.subheader("📊 Magnitude Distribution")
                mag_bins = [2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 10.0]
                mag_labels = ['2.5-3.0', '3.0-4.0', '4.0-5.0', '5.0-6.0', '6.0-7.0', '7.0+']
                
                df_earthquakes['mag_bin'] = pd.cut(df_earthquakes['magnitude'], bins=mag_bins, labels=mag_labels, right=False)
                mag_counts = df_earthquakes['mag_bin'].value_counts().sort_index()
                
                chart_data = pd.DataFrame({
                    'Magnitude Range': mag_counts.index,
                    'Count': mag_counts.values
                })
                
                st.bar_chart(chart_data.set_index('Magnitude Range'))
                
                # Recent earthquakes table
                st.subheader("📍 Recent Earthquakes")
                display_df = df_earthquakes[['time', 'magnitude', 'distance_km', 'location', 'depth_km']].copy()
                display_df['time'] = display_df['time'].dt.strftime('%Y-%m-%d %H:%M')
                display_df['distance_km'] = display_df['distance_km'].round(1)
                st.dataframe(display_df.head(20), use_container_width=True)
                
            else:
                st.success("✅ No earthquakes detected in the selected area and time period.")
        else:
            st.error("❌ Failed to fetch earthquake data")

def weather_monitor():
    st.title("🌤️ Weather & Space Weather")
    
    if 'location' not in st.session_state:
        st.info("Please set your location in the Setup page first.")
        return
        
    location = st.session_state['location']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Weather")
        with st.spinner("Fetching weather data..."):
            weather_data = fetch_weather_forecast(location['latitude'], location['longitude'])
            
            if weather_data and 'current_weather' in weather_data:
                current = weather_data['current_weather']
                
                st.metric("Temperature", f"{current['temperature']}°C")
                st.metric("Wind Speed", f"{current['windspeed']} km/h")
                st.metric("Wind Direction", f"{current['winddirection']}°")
                st.metric("Weather Code", current['weathercode'])
            else:
                st.error("Failed to fetch weather data")
    
    with col2:
        st.subheader("Space Weather")
        with st.spinner("Fetching space weather..."):
            space_data = fetch_space_weather()
            
            if space_data:
                kp_value = space_data['kp_index']
                st.metric("Geomagnetic Kp Index", kp_value)
                
                if kp_value != 'N/A':
                    kp_num = float(kp_value)
                    if kp_num >= 5:
                        st.error("🌩️ Geomagnetic Storm Active")
                    elif kp_num >= 4:
                        st.warning("🌤️ Unsettled Geomagnetic Conditions")
                    else:
                        st.success("☀️ Quiet Geomagnetic Conditions")
                
                st.info("""
                **Kp Index Guide:**
                - 0-4: Quiet to unsettled conditions
                - 5: Minor geomagnetic storm
                - 6: Moderate geomagnetic storm  
                - 7-9: Strong to severe geomagnetic storm
                """)
            else:
                st.error("Failed to fetch space weather data")

def setup_page():
    st.title("⚙️ Setup & Configuration")
    
    st.subheader("🌍 Location Setup")
    input_method = st.radio("Input Method:", ["Select City", "Enter Coordinates"])
    
    if input_method == "Select City":
        selected_city = st.selectbox("Choose a city:", list(MAJOR_CITIES.keys()))
        lat, lon = MAJOR_CITIES[selected_city]
        location_data = {
            'latitude': lat,
            'longitude': lon,
            'address': selected_city,
            'success': True
        }
        st.session_state['location'] = location_data
        st.success(f"Selected: {selected_city}")
        
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
        
        location = st.session_state['location']
        st.info(f"**Current Location:** {location['address']} ({location['latitude']:.4f}, {location['longitude']:.4f})")

def report_page():
    st.title("📊 Full Report")
    
    if 'location' not in st.session_state:
        st.info("Please set your location in the Setup page first.")
        return
        
    location = st.session_state['location']
    params = st.session_state.get('params', {'radius_km': 500, 'days_back': 30, 'min_magnitude': 4.0})
    
    if st.button("🔄 Generate Comprehensive Report", type="primary"):
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
            
            report_text = create_simple_report(location, df_earthquakes, weather_data, space_data)
            
            st.markdown(report_text)
            
            # Download as text file
            st.download_button(
                label="📥 Download Report as Text",
                data=report_text,
                file_name=f"disaster_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                type="primary"
            )

# Main app
def main():
    st.sidebar.title("🌍 Navigation")
    
    # Page selection
    page = st.sidebar.radio("Go to:", [
        "Executive Summary",
        "Earthquake Monitor", 
        "Weather & Space", 
        "Setup",
        "Full Report"
    ])
    
    st.sidebar.markdown("---")
    st.sidebar.info("**PanditaData Disaster Intelligence**\n\nProfessional disaster monitoring and space weather reporting.")
    
    if st.sidebar.button("🔄 Refresh All Data"):
        st.rerun()
    
    # Route to selected page
    if page == "Executive Summary":
        executive_summary()
    elif page == "Earthquake Monitor":
        earthquake_monitor()
    elif page == "Weather & Space":
        weather_monitor()
    elif page == "Setup":
        setup_page()
    elif page == "Full Report":
        report_page()

if __name__ == "__main__":
    main()
