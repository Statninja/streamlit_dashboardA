import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="GeoWeather Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Color Theory Palette
COLOR_THEORY = {
    "earth_green": "#1B5E20",
    "deep_blue": "#0D47A1", 
    "warm_amber": "#E65100",
    "rich_clay": "#BF360C",
    "forest_green": "#2E7D32",
    "sky_blue": "#1565C0",
    "sunset_orange": "#EF6C00",
    "storm_gray": "#263238",
    "cream_white": "#FFFFFF",
    "card_white": "#FFFFFF",
    "text_dark": "#000000",
    "text_light": "#424242",
    "border_dark": "#BDBDBD"
}

# Pure CSS - No external dependencies
st.markdown(f"""
<style>
    .main, .stApp {{
        background: {COLOR_THEORY['cream_white']} !important;
        font-family: Arial, sans-serif !important;
    }}
    
    .earth-kpi {{
        background: {COLOR_THEORY['earth_green']} !important;
        color: white !important;
        padding: 20px !important;
        border-radius: 8px !important;
        text-align: center !important;
        margin: 5px !important;
        border: 2px solid {COLOR_THEORY['forest_green']} !important;
    }}
    
    .weather-kpi {{
        background: {COLOR_THEORY['deep_blue']} !important;
        color: white !important;
        padding: 20px !important;
        border-radius: 8px !important;
        text-align: center !important;
        margin: 5px !important;
        border: 2px solid {COLOR_THEORY['sky_blue']} !important;
    }}
    
    .alert-kpi {{
        background: {COLOR_THEORY['warm_amber']} !important;
        color: white !important;
        padding: 20px !important;
        border-radius: 8px !important;
        text-align: center !important;
        margin: 5px !important;
        border: 2px solid {COLOR_THEORY['sunset_orange']} !important;
    }}
    
    .data-card {{
        background: {COLOR_THEORY['card_white']} !important;
        padding: 15px !important;
        border-radius: 8px !important;
        margin: 10px 0 !important;
        border: 2px solid {COLOR_THEORY['border_dark']} !important;
    }}
    
    .section-header {{
        color: {COLOR_THEORY['text_dark']} !important;
        background: {COLOR_THEORY['card_white']} !important;
        padding: 12px 15px !important;
        border-radius: 6px !important;
        border-left: 5px solid {COLOR_THEORY['earth_green']} !important;
        margin: 15px 0 !important;
        font-weight: bold !important;
        font-size: 1.5rem !important;
    }}
    
    .subsection-header {{
        color: {COLOR_THEORY['text_dark']} !important;
        background: {COLOR_THEORY['card_white']} !important;
        padding: 10px 12px !important;
        border-radius: 5px !important;
        border-left: 4px solid {COLOR_THEORY['sky_blue']} !important;
        margin: 10px 0 !important;
        font-weight: bold !important;
        font-size: 1.2rem !important;
    }}
</style>
""", unsafe_allow_html=True)

# Enhanced fallback data
FALLBACK_EARTHQUAKES = [
    {"location": "San Francisco Bay", "magnitude": 4.2, "depth": 10.0, "lat": 37.7749, "lon": -122.4194, "time": "2024-01-15T10:30:00"},
    {"location": "Tokyo Region", "magnitude": 5.1, "depth": 25.0, "lat": 35.6762, "lon": 139.6503, "time": "2024-01-15T08:15:00"},
    {"location": "Jakarta Area", "magnitude": 3.8, "depth": 15.0, "lat": -6.2088, "lon": 106.8456, "time": "2024-01-15T05:45:00"},
    {"location": "Athens Greece", "magnitude": 4.5, "depth": 12.0, "lat": 37.9838, "lon": 23.7275, "time": "2024-01-15T03:20:00"}
]

FALLBACK_ALERTS = [
    {"type": "Storm Warning", "severity": "High", "description": "Heavy rainfall expected in northern regions", "area": "Northern Region"},
    {"type": "Flood Alert", "severity": "Medium", "description": "River levels rising in coastal areas", "area": "Coastal Areas"},
    {"type": "Heat Advisory", "severity": "Medium", "description": "High temperatures expected this week", "area": "Southern Region"}
]

FALLBACK_WEATHER = [
    {"temperature": 22.0, "humidity": 65.0, "pressure": 1013.0, "condition": "Partly Cloudy", "city": "Sample City", "time": "2024-01-15T12:00:00"},
    {"temperature": 18.5, "humidity": 70.0, "pressure": 1015.0, "condition": "Sunny", "city": "Sample City", "time": "2024-01-15T11:00:00"},
    {"temperature": 20.1, "humidity": 68.0, "pressure": 1012.0, "condition": "Cloudy", "city": "Sample City", "time": "2024-01-15T10:00:00"}
]

class GeoWeatherIntelligence:
    def __init__(self):
        self.base_url = "https://panditadata.com"
        
    def get_city_coordinates(self, city_name):
        """Get coordinates with comprehensive city database"""
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
            "mumbai": (19.0760, 72.8777),
            "los angeles": (34.0522, -118.2437),
            "chicago": (41.8781, -87.6298),
            "toronto": (43.6532, -79.3832),
            "moscow": (55.7558, 37.6173),
            "cairo": (30.0444, 31.2357),
            "rio de janeiro": (-22.9068, -43.1729),
            "beijing": (39.9042, 116.4074),
            "seoul": (37.5665, 126.9780),
            "madrid": (40.4168, -3.7038),
            "rome": (41.9028, 12.4964)
        }
        
        city_lower = city_name.lower().strip()
        if city_lower in city_coordinates:
            lat, lon = city_coordinates[city_lower]
            return lat, lon
        else:
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
                
            return (51.5074, -0.1278)  # Default to London
    
    def get_earthquake_data(self):
        """Get earthquake data with better error handling"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/earthquakesd", timeout=10)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Clean and validate the data
                    cleaned_data = []
                    for item in data:
                        if isinstance(item, dict):
                            try:
                                cleaned_item = {
                                    'location': str(item.get('location', 'Unknown')),
                                    'magnitude': float(item.get('magnitude', 0.0)),
                                    'depth': float(item.get('depth', 0.0)),
                                    'lat': float(item.get('lat', 0.0)),
                                    'lon': float(item.get('lon', 0.0)),
                                    'time': str(item.get('time', 'Unknown'))
                                }
                                cleaned_data.append(cleaned_item)
                            except (ValueError, TypeError):
                                continue
                    
                    if cleaned_data:
                        return cleaned_data
        except requests.exceptions.Timeout:
            st.warning("⏰ Earthquake API timeout, using fallback data")
        except requests.exceptions.ConnectionError:
            st.warning("🔌 Earthquake API connection failed, using fallback data")
        except Exception as e:
            st.warning(f"⚠️ Earthquake API error: {str(e)}, using fallback data")
        
        return FALLBACK_EARTHQUAKES
    
    def get_severe_alerts(self):
        """Get alerts with multiple retry attempts"""
        max_retries = 2
        timeout = 6  # Reduced timeout for faster fallback
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}/api/severe_alerts", timeout=timeout)
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        # Clean and validate alert data
                        cleaned_data = []
                        for item in data:
                            if isinstance(item, dict):
                                try:
                                    cleaned_item = {
                                        'type': str(item.get('type', 'Unknown Alert')),
                                        'severity': str(item.get('severity', 'Medium')),
                                        'description': str(item.get('description', 'No description')),
                                        'area': str(item.get('area', 'Unknown Area'))
                                    }
                                    cleaned_data.append(cleaned_item)
                                except (ValueError, TypeError):
                                    continue
                        
                        if cleaned_data:
                            return cleaned_data
                
                if attempt < max_retries:
                    time.sleep(1)  # Wait before retry
                    continue
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                else:
                    st.warning("⏰ Alert API timeout after retries, using fallback data")
            except requests.exceptions.ConnectionError:
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                else:
                    st.warning("🔌 Alert API connection failed after retries, using fallback data")
            except Exception as e:
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                else:
                    st.warning(f"⚠️ Alert API error after retries: {str(e)}, using fallback data")
        
        return FALLBACK_ALERTS
    
    def get_weather_data(self):
        """Get weather data with improved error handling"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/weather_data", timeout=8)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Clean and validate weather data
                    cleaned_data = []
                    for item in data:
                        if isinstance(item, dict):
                            try:
                                cleaned_item = {
                                    'temperature': float(item.get('temperature', 20.0)),
                                    'humidity': float(item.get('humidity', 50.0)),
                                    'pressure': float(item.get('pressure', 1013.0)),
                                    'condition': str(item.get('condition', 'Unknown')),
                                    'city': str(item.get('city', 'Unknown')),
                                    'time': str(item.get('time', 'Unknown'))
                                }
                                cleaned_data.append(cleaned_item)
                            except (ValueError, TypeError):
                                continue
                    
                    if cleaned_data:
                        return cleaned_data
        except requests.exceptions.Timeout:
            st.warning("⏰ Weather API timeout, using fallback data")
        except requests.exceptions.ConnectionError:
            st.warning("🔌 Weather API connection failed, using fallback data")
        except Exception as e:
            st.warning(f"⚠️ Weather API error: {str(e)}, using fallback data")
        
        return FALLBACK_WEATHER

def create_kpi_card(title, value, subtitle, card_type="earth"):
    """Create KPI cards"""
    card_class = {
        "earth": "earth-kpi",
        "weather": "weather-kpi", 
        "alert": "alert-kpi"
    }.get(card_type, "earth-kpi")
    
    return f"""
    <div class="{card_class}">
        <div style="font-size: 1rem; font-weight: bold; margin: 0;">{title}</div>
        <div style="font-size: 1.8rem; font-weight: bold; margin: 8px 0;">{value}</div>
        <div style="font-size: 0.8rem; opacity: 0.9; margin: 0;">{subtitle}</div>
    </div>
    """

def main():
    dashboard = GeoWeatherIntelligence()
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; padding: 15px; background: {COLOR_THEORY["storm_gray"]}; border-radius: 8px; margin: 5px;'>
            <div style="font-size: 2rem; color: white;">🌍</div>
            <h2 style='color: white; margin: 5px 0;'>GeoWeather Intelligence</h2>
            <p style='color: #E0E0E0; margin: 0; font-size: 0.9rem;'>Real-time Earth Analytics</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("**📍 Location Setup**")
        city_name = st.text_input("Enter City Name", "London")
        
        if st.button("🚀 Load Data", use_container_width=True, type="primary"):
            with st.spinner("Loading data..."):
                # Get coordinates
                lat, lon = dashboard.get_city_coordinates(city_name)
                st.success(f"📍 Found coordinates for {city_name}: {lat:.4f}, {lon:.4f}")
                
                # Load all data
                earthquake_data = dashboard.get_earthquake_data()
                alert_data = dashboard.get_severe_alerts()
                weather_data = dashboard.get_weather_data()
                
                st.session_state.update({
                    'city_name': city_name,
                    'lat': lat,
                    'lon': lon,
                    'earthquake_data': earthquake_data,
                    'severe_alerts': alert_data,
                    'weather_data': weather_data,
                    'data_loaded': True
                })
        
        st.markdown("---")
        st.markdown("**🧭 Navigation**")
        page = st.radio("Go to", ["Dashboard", "Data Tables", "Analytics"], label_visibility="collapsed")
        
        st.markdown("---")
        st.markdown(f"""
        <div style='color: #E0E0E0; font-size: 0.8rem;'>
        <p><strong>📊 Live APIs:</strong></p>
        <ul>
            <li>✅ Earthquakes</li>
            <li>⚠️ Alerts (Fallback)</li>
            <li>✅ Weather</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    # Main content
    if 'data_loaded' not in st.session_state:
        show_welcome()
    else:
        if page == "Dashboard":
            show_dashboard()
        elif page == "Data Tables":
            show_data_tables()
        else:
            show_analytics()

def show_welcome():
    """Welcome page"""
    st.markdown("<div class='section-header'>🚀 Welcome to GeoWeather Intelligence</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class='data-card'>
            <h3>Get Started</h3>
            <p>Enter a city name and click <strong>Load Data</strong> to begin analysis:</p>
            <ul>
                <li>🌋 Real-time earthquake monitoring</li>
                <li>⛈️ Weather alerts and warnings</li>
                <li>🌤️ Live weather data analytics</li>
                <li>📊 Interactive data exploration</li>
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
                <li>Berlin</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def show_dashboard():
    """Main dashboard"""
    city = st.session_state.city_name
    lat = st.session_state.lat
    lon = st.session_state.lon
    
    st.markdown(f"<div class='section-header'>🌍 Earth Analytics - {city}</div>", unsafe_allow_html=True)
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(create_kpi_card("📍 Location", city, "Selected City", "earth"), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_kpi_card("🌐 Coordinates", f"{lat:.2f}, {lon:.2f}", "Latitude, Longitude", "weather"), unsafe_allow_html=True)
    
    with col3:
        eq_count = len(st.session_state.earthquake_data)
        st.markdown(create_kpi_card("🌋 Earthquakes", str(eq_count), "Recent Events", "earth"), unsafe_allow_html=True)
    
    with col4:
        alert_count = len(st.session_state.severe_alerts)
        st.markdown(create_kpi_card("⚠️ Alerts", str(alert_count), "Active Warnings", "alert"), unsafe_allow_html=True)
    
    # Earthquake Data
    st.markdown("<div class='subsection-header'>🌋 Recent Earthquake Data</div>", unsafe_allow_html=True)
    
    earthquake_data = st.session_state.earthquake_data
    if earthquake_data:
        try:
            eq_df = pd.DataFrame(earthquake_data)
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                if 'magnitude' in eq_df.columns:
                    st.metric("Average Magnitude", f"{eq_df['magnitude'].mean():.1f}")
            with col2:
                if 'depth' in eq_df.columns:
                    st.metric("Max Depth", f"{eq_df['depth'].max():.1f} km")
            with col3:
                st.metric("Total Events", len(eq_df))
            
            # Show data table
            display_cols = [col for col in ['location', 'magnitude', 'depth', 'time'] if col in eq_df.columns]
            if display_cols:
                st.dataframe(eq_df[display_cols].head(8), use_container_width=True)
                
        except Exception as e:
            st.error(f"Error processing earthquake data: {str(e)}")
    else:
        st.info("No earthquake data available")
    
    # Weather Alerts
    st.markdown("<div class='subsection-header'>⚠️ Active Weather Alerts</div>", unsafe_allow_html=True)
    
    alerts_data = st.session_state.severe_alerts
    if alerts_data:
        try:
            alerts_df = pd.DataFrame(alerts_data)
            
            for _, alert in alerts_df.iterrows():
                alert_type = alert.get('type', 'Unknown')
                severity = alert.get('severity', 'Medium')
                description = alert.get('description', 'No description')
                area = alert.get('area', 'Unknown area')
                
                st.markdown(f"""
                <div class='data-card'>
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <h4 style="margin: 0; color: {COLOR_THEORY['text_dark']};">{alert_type}</h4>
                        <span style="background: {COLOR_THEORY['warm_amber']}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold;">
                            {severity}
                        </span>
                    </div>
                    <p style="margin: 5px 0; color: {COLOR_THEORY['text_light']};"><strong>Area:</strong> {area}</p>
                    <p style="margin: 0; color: {COLOR_THEORY['text_light']};">{description}</p>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error processing alert data: {str(e)}")
    else:
        st.info("No active weather alerts")
    
    # Weather Data
    st.markdown("<div class='subsection-header'>🌤️ Weather Observations</div>", unsafe_allow_html=True)
    
    weather_data = st.session_state.weather_data
    if weather_data:
        try:
            weather_df = pd.DataFrame(weather_data)
            
            if not weather_df.empty:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if 'temperature' in weather_df.columns:
                        st.metric("Avg Temperature", f"{weather_df['temperature'].mean():.1f}°C")
                with col2:
                    if 'humidity' in weather_df.columns:
                        st.metric("Avg Humidity", f"{weather_df['humidity'].mean():.1f}%")
                with col3:
                    if 'pressure' in weather_df.columns:
                        st.metric("Avg Pressure", f"{weather_df['pressure'].mean():.1f} hPa")
                with col4:
                    st.metric("Data Points", len(weather_df))
                
                # Show weather table
                weather_cols = [col for col in ['temperature', 'humidity', 'pressure', 'condition'] if col in weather_df.columns]
                if weather_cols:
                    st.dataframe(weather_df[weather_cols].head(6), use_container_width=True)
                    
        except Exception as e:
            st.error(f"Error processing weather data: {str(e)}")
    else:
        st.info("No weather data available")

def show_data_tables():
    """Data tables view"""
    st.markdown("<div class='section-header'>📋 Raw Data Explorer</div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🌋 Earthquakes", "⚠️ Alerts", "🌤️ Weather"])
    
    with tab1:
        st.markdown("<div class='subsection-header'>Earthquake Data</div>", unsafe_allow_html=True)
        if st.session_state.earthquake_data:
            try:
                eq_df = pd.DataFrame(st.session_state.earthquake_data)
                st.dataframe(eq_df, use_container_width=True)
                
                # Statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Records", len(eq_df))
                with col2:
                    if 'magnitude' in eq_df.columns:
                        st.metric("Max Magnitude", f"{eq_df['magnitude'].max():.1f}")
                with col3:
                    if 'depth' in eq_df.columns:
                        st.metric("Avg Depth", f"{eq_df['depth'].mean():.1f} km")
            except Exception as e:
                st.error(f"Error displaying earthquake data: {str(e)}")
    
    with tab2:
        st.markdown("<div class='subsection-header'>Weather Alerts</div>", unsafe_allow_html=True)
        if st.session_state.severe_alerts:
            try:
                alerts_df = pd.DataFrame(st.session_state.severe_alerts)
                st.dataframe(alerts_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying alert data: {str(e)}")
    
    with tab3:
        st.markdown("<div class='subsection-header'>Weather Data</div>", unsafe_allow_html=True)
        if st.session_state.weather_data:
            try:
                weather_df = pd.DataFrame(st.session_state.weather_data)
                st.dataframe(weather_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying weather data: {str(e)}")

def show_analytics():
    """Analytics view"""
    st.markdown("<div class='section-header'>📊 Data Analytics</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='subsection-header'>Earthquake Statistics</div>", unsafe_allow_html=True)
        if st.session_state.earthquake_data:
            try:
                eq_df = pd.DataFrame(st.session_state.earthquake_data)
                
                if not eq_df.empty and 'magnitude' in eq_df.columns:
                    st.metric("Maximum Magnitude", f"{eq_df['magnitude'].max():.2f}")
                    st.metric("Minimum Magnitude", f"{eq_df['magnitude'].min():.2f}")
                    st.metric("Average Magnitude", f"{eq_df['magnitude'].mean():.2f}")
                    st.metric("Total Earthquakes", len(eq_df))
            except Exception as e:
                st.error(f"Error calculating earthquake statistics: {str(e)}")
    
    with col2:
        st.markdown("<div class='subsection-header'>Weather Statistics</div>", unsafe_allow_html=True)
        if st.session_state.weather_data:
            try:
                weather_df = pd.DataFrame(st.session_state.weather_data)
                
                if not weather_df.empty:
                    if 'temperature' in weather_df.columns:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Max Temperature", f"{weather_df['temperature'].max():.1f}°C")
                        with col2:
                            st.metric("Min Temperature", f"{weather_df['temperature'].min():.1f}°C")
            except Exception as e:
                st.error(f"Error calculating weather statistics: {str(e)}")

if __name__ == "__main__":
    main()
