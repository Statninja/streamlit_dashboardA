import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="GeoWeather Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Advanced Color Theory Palette
COLOR_THEORY = {
    "earth_green": "#2E8B57",
    "deep_blue": "#1E6FA9", 
    "warm_amber": "#FF8C42",
    "rich_clay": "#D35400",
    "forest_green": "#228B22",
    "sky_blue": "#4682B4",
    "sunset_orange": "#FF6B35",
    "storm_gray": "#2C3E50",
    "cream_white": "#FDF6E3",
    "card_white": "#FFFFFF",
    "text_dark": "#2C3E50",
    "text_light": "#7F8C8D"
}

# Custom CSS
st.markdown(f"""
<style>
    .main {{
        background: linear-gradient(135deg, {COLOR_THEORY['cream_white']}, #E8F4F8);
    }}
    .stApp {{
        background: linear-gradient(135deg, {COLOR_THEORY['cream_white']}, #E8F4F8);
    }}
    .earth-kpi {{
        background: linear-gradient(135deg, {COLOR_THEORY['earth_green']}, {COLOR_THEORY['forest_green']});
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 5px;
    }}
    .weather-kpi {{
        background: linear-gradient(135deg, {COLOR_THEORY['deep_blue']}, {COLOR_THEORY['sky_blue']});
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 5px;
    }}
    .data-card {{
        background: {COLOR_THEORY['card_white']};
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid {COLOR_THEORY['earth_green']};
    }}
    .section-header {{
        color: {COLOR_THEORY['storm_gray']};
        border-bottom: 2px solid {COLOR_THEORY['earth_green']};
        padding-bottom: 10px;
        margin: 20px 0;
    }}
</style>
""", unsafe_allow_html=True)

# Fallback data in case APIs are blocked
FALLBACK_EARTHQUAKES = [
    {"location": "San Francisco", "magnitude": 4.2, "depth": 10, "lat": 37.7749, "lon": -122.4194, "time": "2024-01-15T10:30:00"},
    {"location": "Tokyo", "magnitude": 5.1, "depth": 25, "lat": 35.6762, "lon": 139.6503, "time": "2024-01-15T08:15:00"},
    {"location": "Jakarta", "magnitude": 3.8, "depth": 15, "lat": -6.2088, "lon": 106.8456, "time": "2024-01-15T05:45:00"}
]

FALLBACK_ALERTS = [
    {"type": "Storm Warning", "severity": "High", "description": "Heavy rainfall expected", "area": "Northern Region"},
    {"type": "Flood Alert", "severity": "Medium", "description": "River levels rising", "area": "Coastal Areas"}
]

FALLBACK_WEATHER = [
    {"temperature": 22, "humidity": 65, "pressure": 1013, "condition": "Partly Cloudy", "city": "Sample City"}
]

class GeoWeatherIntelligence:
    def __init__(self):
        self.base_url = "https://panditadata.com"
        
    def get_city_coordinates(self, city_name):
        """Get latitude and longitude for a city with fallback"""
        try:
            # Use a simple coordinate lookup as fallback
            city_coordinates = {
                "london": (51.5074, -0.1278),
                "new york": (40.7128, -74.0060),
                "tokyo": (35.6762, 139.6503),
                "paris": (48.8566, 2.3522),
                "sydney": (-33.8688, 151.2093),
                "delhi": (28.7041, 77.1025),
                "dubai": (25.2048, 55.2708),
                "singapore": (1.3521, 103.8198),
                "berlin": (52.5200, 13.4050),
                "mumbai": (19.0760, 72.8777)
            }
            
            city_lower = city_name.lower().strip()
            if city_lower in city_coordinates:
                return city_coordinates[city_lower]
            
            # Try API as fallback
            try:
                response = requests.get(f"{self.base_url}/weather/{city_name}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    lat = data.get('lat')
                    lon = data.get('lon')
                    if lat and lon:
                        return float(lat), float(lon)
            except:
                pass
                
            # Default to London if city not found
            return (51.5074, -0.1278)
            
        except Exception as e:
            st.error(f"Using default coordinates for {city_name}")
            return (51.5074, -0.1278)
    
    def get_earthquake_data(self):
        """Get earthquake data with fallback"""
        try:
            response = requests.get(f"{self.base_url}/earthquakesd", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data
        except:
            pass
        return FALLBACK_EARTHQUAKES
    
    def get_severe_alerts(self):
        """Get severe weather alerts with fallback"""
        try:
            response = requests.get(f"{self.base_url}/api/severe_alerts", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data
        except:
            pass
        return FALLBACK_ALERTS
    
    def get_weather_data(self):
        """Get weather data with fallback"""
        try:
            response = requests.get(f"{self.base_url}/weather_data", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data
        except:
            pass
        return FALLBACK_WEATHER

def main():
    dashboard = GeoWeatherIntelligence()
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"<h2 style='color: {COLOR_THEORY['earth_green']};'>🌍 GeoWeather Dashboard</h2>", 
                   unsafe_allow_html=True)
        
        st.markdown("---")
        
        # City input
        city_name = st.text_input("Enter City Name", "London")
        
        if st.button("Get Data", use_container_width=True):
            with st.spinner("Loading data..."):
                lat, lon = dashboard.get_city_coordinates(city_name)
                
                st.session_state.update({
                    'city_name': city_name,
                    'lat': lat,
                    'lon': lon,
                    'earthquake_data': dashboard.get_earthquake_data(),
                    'severe_alerts': dashboard.get_severe_alerts(),
                    'weather_data': dashboard.get_weather_data(),
                    'data_loaded': True
                })
        
        st.markdown("---")
        st.markdown("**Navigation**")
        page = st.radio("Go to", ["Dashboard", "Data Tables"])
        
        st.markdown("---")
        st.info("💡 Tip: Use common city names for best results")

    # Main content
    if 'data_loaded' not in st.session_state:
        show_welcome()
    else:
        if page == "Dashboard":
            show_dashboard()
        else:
            show_tables()

def show_welcome():
    """Welcome page"""
    st.markdown(f"<h1 class='section-header'>Welcome to GeoWeather Intelligence</h1>", 
               unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class='data-card'>
            <h3>🚀 Get Started</h3>
            <p>Enter a city name in the sidebar and click <strong>Get Data</strong> to begin exploring:</p>
            <ul>
                <li>🌋 Real-time earthquake data</li>
                <li>⛈️ Severe weather alerts</li>
                <li>🌤️ Weather patterns and trends</li>
                <li>📊 Interactive data visualizations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='data-card'>
            <h3>📍 Popular Cities</h3>
            <p>Try these cities:</p>
            <ul>
                <li>London</li>
                <li>New York</li>
                <li>Tokyo</li>
                <li>Paris</li>
                <li>Sydney</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def show_dashboard():
    """Main dashboard view"""
    city = st.session_state.city_name
    lat = st.session_state.lat
    lon = st.session_state.lon
    
    st.markdown(f"<h1 class='section-header'>🌤️ Dashboard - {city}</h1>", 
               unsafe_allow_html=True)
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='earth-kpi'>
            <h3>📍 Location</h3>
            <h2>{city}</h2>
            <p>Selected City</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='weather-kpi'>
            <h3>🌐 Coordinates</h3>
            <h2>{lat:.2f}, {lon:.2f}</h2>
            <p>Latitude, Longitude</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        eq_count = len(st.session_state.earthquake_data)
        st.markdown(f"""
        <div class='earth-kpi'>
            <h3>🌋 Earthquakes</h3>
            <h2>{eq_count}</h2>
            <p>Recent Events</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        alert_count = len(st.session_state.severe_alerts)
        st.markdown(f"""
        <div class='weather-kpi'>
            <h3>⚠️ Alerts</h3>
            <h2>{alert_count}</h2>
            <p>Active Warnings</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Earthquake Data
    st.markdown(f"<h2 class='section-header'>🌋 Recent Earthquakes</h2>", 
               unsafe_allow_html=True)
    
    if st.session_state.earthquake_data:
        eq_df = pd.DataFrame(st.session_state.earthquake_data)
        
        # Display earthquake metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'magnitude' in eq_df.columns:
                avg_mag = eq_df['magnitude'].mean()
                st.metric("Average Magnitude", f"{avg_mag:.1f}")
        
        with col2:
            if 'depth' in eq_df.columns:
                max_depth = eq_df['depth'].max()
                st.metric("Max Depth", f"{max_depth} km")
        
        with col3:
            st.metric("Total Events", len(eq_df))
        
        # Show earthquake table
        display_cols = [col for col in ['location', 'magnitude', 'depth', 'time'] 
                       if col in eq_df.columns]
        if display_cols:
            st.dataframe(eq_df[display_cols].head(8), use_container_width=True)
    
    # Weather Alerts
    st.markdown(f"<h2 class='section-header'>⚠️ Weather Alerts</h2>", 
               unsafe_allow_html=True)
    
    if st.session_state.severe_alerts:
        alerts_df = pd.DataFrame(st.session_state.severe_alerts)
        
        for _, alert in alerts_df.iterrows():
            alert_type = alert.get('type', 'Unknown')
            severity = alert.get('severity', 'Medium')
            description = alert.get('description', 'No description')
            
            st.markdown(f"""
            <div class='data-card' style='border-left-color: {COLOR_THEORY["warm_amber"]};'>
                <div style='display: flex; justify-content: space-between; align-items: start;'>
                    <div>
                        <h4 style='margin: 0; color: {COLOR_THEORY["storm_gray"]};'>{alert_type}</h4>
                        <p style='margin: 5px 0; color: {COLOR_THEORY["text_light"]};'>{description}</p>
                    </div>
                    <span style='background: {COLOR_THEORY["warm_amber"]}; color: white; padding: 5px 10px; border-radius: 15px; font-size: 0.8em;'>
                        {severity}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active weather alerts")
    
    # Weather Data
    st.markdown(f"<h2 class='section-header'>🌤️ Weather Data</h2>", 
               unsafe_allow_html=True)
    
    if st.session_state.weather_data:
        weather_df = pd.DataFrame(st.session_state.weather_data)
        
        if not weather_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if 'temperature' in weather_df.columns:
                    avg_temp = weather_df['temperature'].mean()
                    st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
            
            with col2:
                if 'humidity' in weather_df.columns:
                    avg_humidity = weather_df['humidity'].mean()
                    st.metric("Avg Humidity", f"{avg_humidity:.1f}%")
            
            with col3:
                if 'pressure' in weather_df.columns:
                    avg_pressure = weather_df['pressure'].mean()
                    st.metric("Avg Pressure", f"{avg_pressure:.1f} hPa")
            
            with col4:
                st.metric("Data Points", len(weather_df))
            
            # Show weather data table
            weather_cols = [col for col in ['temperature', 'humidity', 'pressure', 'condition'] 
                          if col in weather_df.columns]
            if weather_cols:
                st.dataframe(weather_df[weather_cols].head(6), use_container_width=True)

def show_tables():
    """Data tables view"""
    st.markdown(f"<h1 class='section-header'>📊 Data Tables</h1>", 
               unsafe_allow_html=True)
    
    # Tabs for different data types
    tab1, tab2, tab3 = st.tabs(["🌋 Earthquakes", "⚠️ Alerts", "🌤️ Weather"])
    
    with tab1:
        st.subheader("Earthquake Data")
        if st.session_state.earthquake_data:
            eq_df = pd.DataFrame(st.session_state.earthquake_data)
            st.dataframe(eq_df, use_container_width=True)
            
            # Statistics
            st.subheader("Earthquake Statistics")
            if not eq_df.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Records", len(eq_df))
                with col2:
                    if 'magnitude' in eq_df.columns:
                        st.metric("Max Magnitude", f"{eq_df['magnitude'].max():.1f}")
                with col3:
                    if 'depth' in eq_df.columns:
                        st.metric("Average Depth", f"{eq_df['depth'].mean():.1f} km")
    
    with tab2:
        st.subheader("Weather Alerts")
        if st.session_state.severe_alerts:
            alerts_df = pd.DataFrame(st.session_state.severe_alerts)
            st.dataframe(alerts_df, use_container_width=True)
            
            # Alert summary
            if 'severity' in alerts_df.columns:
                st.subheader("Alert Summary")
                severity_counts = alerts_df['severity'].value_counts()
                for severity, count in severity_counts.items():
                    st.write(f"**{severity}**: {count} alerts")
    
    with tab3:
        st.subheader("Weather Data")
        if st.session_state.weather_data:
            weather_df = pd.DataFrame(st.session_state.weather_data)
            st.dataframe(weather_df, use_container_width=True)
            
            # Weather summary
            st.subheader("Weather Summary")
            if not weather_df.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if 'temperature' in weather_df.columns:
                        st.metric("Avg Temp", f"{weather_df['temperature'].mean():.1f}°C")
                with col2:
                    if 'humidity' in weather_df.columns:
                        st.metric("Avg Humidity", f"{weather_df['humidity'].mean():.1f}%")
                with col3:
                    st.metric("Total Records", len(weather_df))

if __name__ == "__main__":
    main()
