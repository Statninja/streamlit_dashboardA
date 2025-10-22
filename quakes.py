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

# Enhanced Color Theory Palette with better contrast
COLOR_THEORY = {
    # Primary Colors - High Contrast
    "earth_green": "#1B5E20",      # Darker green for better contrast
    "deep_blue": "#0D47A1",        # Darker blue for better contrast
    "warm_amber": "#E65100",       # Darker amber for better contrast
    "rich_clay": "#BF360C",        # Darker clay for better contrast
    
    # Secondary Colors
    "forest_green": "#2E7D32",
    "sky_blue": "#1565C0",
    "sunset_orange": "#EF6C00",
    "storm_gray": "#263238",
    
    # Background & UI - Solid, non-transparent
    "cream_white": "#FFFFFF",      # Pure white background
    "card_white": "#FFFFFF",       # Solid white cards
    "text_dark": "#000000",        # Pure black for best contrast
    "text_light": "#424242",       # Dark gray for secondary text
    "border_dark": "#BDBDBD"       # Border color
}

# Enhanced CSS with solid backgrounds and better contrast
st.markdown(f"""
<style>
    .main {{
        background: {COLOR_THEORY['cream_white']} !important;
    }}
    
    .stApp {{
        background: {COLOR_THEORY['cream_white']} !important;
    }}
    
    /* Solid KPI Cards with high contrast */
    .earth-kpi {{
        background: {COLOR_THEORY['earth_green']} !important;
        color: white !important;
        padding: 25px !important;
        border-radius: 10px !important;
        text-align: center !important;
        margin: 10px !important;
        border: 2px solid {COLOR_THEORY['forest_green']} !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }}
    
    .weather-kpi {{
        background: {COLOR_THEORY['deep_blue']} !important;
        color: white !important;
        padding: 25px !important;
        border-radius: 10px !important;
        text-align: center !important;
        margin: 10px !important;
        border: 2px solid {COLOR_THEORY['sky_blue']} !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }}
    
    .alert-kpi {{
        background: {COLOR_THEORY['warm_amber']} !important;
        color: white !important;
        padding: 25px !important;
        border-radius: 10px !important;
        text-align: center !important;
        margin: 10px !important;
        border: 2px solid {COLOR_THEORY['sunset_orange']} !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }}
    
    /* Solid Data Cards */
    .data-card {{
        background: {COLOR_THEORY['card_white']} !important;
        padding: 20px !important;
        border-radius: 10px !important;
        margin: 15px 0 !important;
        border: 2px solid {COLOR_THEORY['border_dark']} !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }}
    
    /* High Contrast Headers */
    .section-header {{
        color: {COLOR_THEORY['text_dark']} !important;
        background: {COLOR_THEORY['card_white']} !important;
        padding: 15px 20px !important;
        border-radius: 8px !important;
        border-left: 5px solid {COLOR_THEORY['earth_green']} !important;
        margin: 20px 0 !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }}
    
    .subsection-header {{
        color: {COLOR_THEORY['text_dark']} !important;
        background: {COLOR_THEORY['card_white']} !important;
        padding: 12px 15px !important;
        border-radius: 6px !important;
        border-left: 4px solid {COLOR_THEORY['sky_blue']} !important;
        margin: 15px 0 !important;
        font-weight: 600 !important;
        font-size: 1.4rem !important;
    }}
    
    /* High contrast text */
    .kpi-title {{
        color: white !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        margin: 0 !important;
    }}
    
    .kpi-value {{
        color: white !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
        margin: 10px 0 !important;
    }}
    
    .kpi-subtitle {{
        color: rgba(255,255,255,0.9) !important;
        font-size: 0.9rem !important;
        margin: 0 !important;
    }}
    
    /* Solid sidebar */
    .sidebar .sidebar-content {{
        background: {COLOR_THEORY['storm_gray']} !important;
        color: white !important;
    }}
</style>
""", unsafe_allow_html=True)

# Enhanced fallback data with consistent structure
FALLBACK_EARTHQUAKES = [
    {"location": "San Francisco", "magnitude": 4.2, "depth": 10.0, "lat": 37.7749, "lon": -122.4194, "time": "2024-01-15T10:30:00"},
    {"location": "Tokyo", "magnitude": 5.1, "depth": 25.0, "lat": 35.6762, "lon": 139.6503, "time": "2024-01-15T08:15:00"},
    {"location": "Jakarta", "magnitude": 3.8, "depth": 15.0, "lat": -6.2088, "lon": 106.8456, "time": "2024-01-15T05:45:00"},
    {"location": "Athens", "magnitude": 4.5, "depth": 12.0, "lat": 37.9838, "lon": 23.7275, "time": "2024-01-15T03:20:00"}
]

FALLBACK_ALERTS = [
    {"type": "Storm Warning", "severity": "High", "description": "Heavy rainfall expected", "area": "Northern Region"},
    {"type": "Flood Alert", "severity": "Medium", "description": "River levels rising", "area": "Coastal Areas"}
]

FALLBACK_WEATHER = [
    {"temperature": 22.0, "humidity": 65.0, "pressure": 1013.0, "condition": "Partly Cloudy", "city": "Sample City", "time": "2024-01-15T12:00:00"}
]

class GeoWeatherIntelligence:
    def __init__(self):
        self.base_url = "https://panditadata.com"
        
    def get_city_coordinates(self, city_name):
        """Get latitude and longitude for a city with enhanced fallback"""
        try:
            # Enhanced coordinate database
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
                "cairo": (30.0444, 31.2357)
            }
            
            city_lower = city_name.lower().strip()
            if city_lower in city_coordinates:
                return city_coordinates[city_lower]
            
            # Try API as secondary option
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
        """Get earthquake data with robust error handling"""
        try:
            response = requests.get(f"{self.base_url}/earthquakesd", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Validate and clean earthquake data
                    cleaned_data = []
                    for item in data:
                        if isinstance(item, dict):
                            # Ensure all required fields exist with proper types
                            cleaned_item = {
                                'location': str(item.get('location', 'Unknown')),
                                'magnitude': float(item.get('magnitude', 0.0)),
                                'depth': float(item.get('depth', 0.0)),
                                'lat': float(item.get('lat', 0.0)),
                                'lon': float(item.get('lon', 0.0)),
                                'time': str(item.get('time', 'Unknown'))
                            }
                            cleaned_data.append(cleaned_item)
                    return cleaned_data if cleaned_data else FALLBACK_EARTHQUAKES
        except Exception as e:
            st.error(f"Error loading earthquake data: {str(e)}")
        
        return FALLBACK_EARTHQUAKES
    
    def get_severe_alerts(self):
        """Get severe weather alerts with robust error handling"""
        try:
            response = requests.get(f"{self.base_url}/api/severe_alerts", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Clean alert data
                    cleaned_data = []
                    for item in data:
                        if isinstance(item, dict):
                            cleaned_item = {
                                'type': str(item.get('type', 'Unknown Alert')),
                                'severity': str(item.get('severity', 'Medium')),
                                'description': str(item.get('description', 'No description')),
                                'area': str(item.get('area', 'Unknown Area'))
                            }
                            cleaned_data.append(cleaned_item)
                    return cleaned_data if cleaned_data else FALLBACK_ALERTS
        except Exception as e:
            st.error(f"Error loading alert data: {str(e)}")
        
        return FALLBACK_ALERTS
    
    def get_weather_data(self):
        """Get weather data with robust error handling"""
        try:
            response = requests.get(f"{self.base_url}/weather_data", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Clean weather data
                    cleaned_data = []
                    for item in data:
                        if isinstance(item, dict):
                            cleaned_item = {
                                'temperature': float(item.get('temperature', 20.0)),
                                'humidity': float(item.get('humidity', 50.0)),
                                'pressure': float(item.get('pressure', 1013.0)),
                                'condition': str(item.get('condition', 'Unknown')),
                                'city': str(item.get('city', 'Unknown')),
                                'time': str(item.get('time', 'Unknown'))
                            }
                            cleaned_data.append(cleaned_item)
                    return cleaned_data if cleaned_data else FALLBACK_WEATHER
        except Exception as e:
            st.error(f"Error loading weather data: {str(e)}")
        
        return FALLBACK_WEATHER

def create_kpi_card(title, value, subtitle, card_type="earth"):
    """Create consistent KPI cards with high contrast"""
    if card_type == "weather":
        card_class = "weather-kpi"
    elif card_type == "alert":
        card_class = "alert-kpi"
    else:
        card_class = "earth-kpi"
    
    return f"""
    <div class="{card_class}">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-subtitle">{subtitle}</div>
    </div>
    """

def main():
    dashboard = GeoWeatherIntelligence()
    
    # Sidebar with solid background
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; padding: 20px 0; background: {COLOR_THEORY["storm_gray"]}; border-radius: 10px; margin: 10px;'>
            <h1 style='color: white; margin: 0; font-size: 2.5rem;'>🌍</h1>
            <h2 style='color: white; margin: 10px 0;'>GeoWeather Intelligence</h2>
            <p style='color: #E0E0E0; margin: 0;'>Real-time Earth & Weather Analytics</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # City input
        st.markdown(f"<h3 style='color: white; background: {COLOR_THEORY['storm_gray']}; padding: 10px; border-radius: 5px;'>📍 Location Setup</h3>", 
                   unsafe_allow_html=True)
        city_name = st.text_input("Enter City Name", "London", key="city_input")
        
        if st.button("🚀 Get GeoWeather Data", use_container_width=True, type="primary"):
            with st.spinner("🛰️ Loading data..."):
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
        
        # Navigation
        st.markdown(f"<h3 style='color: white; background: {COLOR_THEORY['storm_gray']}; padding: 10px; border-radius: 5px;'>🧭 Navigation</h3>", 
                   unsafe_allow_html=True)
        page = st.radio("Select View", 
                       ["📊 Overview Dashboard", "📈 Analytics", "📋 Raw Data"],
                       label_visibility="collapsed")
        
        st.markdown("---")
        st.markdown(f"""
        <div style='color: #E0E0E0; background: {COLOR_THEORY['storm_gray']}; padding: 15px; border-radius: 8px;'>
            <p><strong>🌐 Data Sources:</strong></p>
            <ul>
                <li>Seismic Activity API</li>
                <li>Weather Intelligence</li>
                <li>Alert Systems</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Main content
    if 'data_loaded' not in st.session_state:
        show_welcome()
    else:
        if "Overview Dashboard" in page:
            show_dashboard()
        elif "Analytics" in page:
            show_analytics()
        else:
            show_raw_data()

def show_welcome():
    """Welcome page with solid backgrounds"""
    st.markdown(f"<div class='section-header'>🚀 Welcome to GeoWeather Intelligence</div>", 
               unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div class='data-card'>
            <h3 style='color: {COLOR_THEORY["text_dark"]};'>Get Started</h3>
            <p style='color: {COLOR_THEORY["text_light"]};'>Enter a city name in the sidebar and click <strong>Get GeoWeather Data</strong> to begin exploring:</p>
            <ul style='color: {COLOR_THEORY["text_light"]};'>
                <li>🌋 Real-time earthquake data</li>
                <li>⛈️ Severe weather alerts</li>
                <li>🌤️ Weather patterns and trends</li>
                <li>📊 Interactive data visualizations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='data-card'>
            <h3 style='color: {COLOR_THEORY["text_dark"]};'>📍 Popular Cities</h3>
            <p style='color: {COLOR_THEORY["text_light"]};'>Try these cities:</p>
            <ul style='color: {COLOR_THEORY["text_light"]};'>
                <li>London</li>
                <li>New York</li>
                <li>Tokyo</li>
                <li>Paris</li>
                <li>Sydney</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def show_dashboard():
    """Main dashboard with fixed data handling"""
    city = st.session_state.city_name
    lat = st.session_state.lat
    lon = st.session_state.lon
    
    st.markdown(f"<div class='section-header'>🌐 Earth Intelligence - {city}</div>", 
               unsafe_allow_html=True)
    
    # KPI Cards - Fixed with proper data handling
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(create_kpi_card("📍 Location", city, "Selected City", "earth"), 
                   unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_kpi_card("🌐 Coordinates", f"{lat:.2f}, {lon:.2f}", "Latitude, Longitude", "weather"), 
                   unsafe_allow_html=True)
    
    with col3:
        eq_count = len(st.session_state.earthquake_data)
        st.markdown(create_kpi_card("🌋 Earthquakes", str(eq_count), "Recent Events", "earth"), 
                   unsafe_allow_html=True)
    
    with col4:
        alert_count = len(st.session_state.severe_alerts)
        st.markdown(create_kpi_card("⚠️ Alerts", str(alert_count), "Active Warnings", "alert"), 
                   unsafe_allow_html=True)
    
    # Earthquake Data Section - Fixed with robust DataFrame creation
    st.markdown(f"<div class='subsection-header'>🌋 Recent Earthquakes</div>", 
               unsafe_allow_html=True)
    
    earthquake_data = st.session_state.earthquake_data
    
    if earthquake_data:
        try:
            # Create DataFrame with error handling
            eq_df = pd.DataFrame(earthquake_data)
            
            # Display earthquake metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'magnitude' in eq_df.columns:
                    avg_mag = eq_df['magnitude'].mean()
                    st.metric("Average Magnitude", f"{avg_mag:.1f}")
                else:
                    st.metric("Average Magnitude", "N/A")
            
            with col2:
                if 'depth' in eq_df.columns:
                    max_depth = eq_df['depth'].max()
                    st.metric("Max Depth", f"{max_depth:.1f} km")
                else:
                    st.metric("Max Depth", "N/A")
            
            with col3:
                st.metric("Total Events", len(eq_df))
            
            # Show earthquake table with error handling
            st.markdown(f"""
            <div class='data-card'>
                <h4 style='color: {COLOR_THEORY["text_dark"]}; margin-bottom: 15px;'>Earthquake Data Table</h4>
            </div>
            """, unsafe_allow_html=True)
            
            display_cols = [col for col in ['location', 'magnitude', 'depth', 'time'] 
                           if col in eq_df.columns]
            if display_cols:
                st.dataframe(eq_df[display_cols].head(8), use_container_width=True)
            else:
                st.info("No earthquake data columns available for display")
                
        except Exception as e:
            st.error(f"Error displaying earthquake data: {str(e)}")
            st.info("Showing raw earthquake data:")
            st.json(earthquake_data[:3])  # Show first 3 items for debugging
    else:
        st.info("No earthquake data available")
    
    # Weather Alerts Section
    st.markdown(f"<div class='subsection-header'>⚠️ Weather Alerts</div>", 
               unsafe_allow_html=True)
    
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
                <div class='data-card' style='border-left: 4px solid {COLOR_THEORY["warm_amber"]};'>
                    <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;'>
                        <h4 style='color: {COLOR_THEORY["text_dark"]}; margin: 0;'>{alert_type}</h4>
                        <span style='background: {COLOR_THEORY["warm_amber"]}; color: white; padding: 5px 10px; border-radius: 15px; font-size: 0.8em; font-weight: bold;'>
                            {severity}
                        </span>
                    </div>
                    <p style='color: {COLOR_THEORY["text_light"]}; margin: 5px 0;'><strong>Area:</strong> {area}</p>
                    <p style='color: {COLOR_THEORY["text_light"]}; margin: 0;'>{description}</p>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error displaying alert data: {str(e)}")
    else:
        st.info("No active weather alerts")
    
    # Weather Data Section
    st.markdown(f"<div class='subsection-header'>🌤️ Weather Data</div>", 
               unsafe_allow_html=True)
    
    weather_data = st.session_state.weather_data
    
    if weather_data:
        try:
            weather_df = pd.DataFrame(weather_data)
            
            if not weather_df.empty:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if 'temperature' in weather_df.columns:
                        avg_temp = weather_df['temperature'].mean()
                        st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
                    else:
                        st.metric("Avg Temperature", "N/A")
                
                with col2:
                    if 'humidity' in weather_df.columns:
                        avg_humidity = weather_df['humidity'].mean()
                        st.metric("Avg Humidity", f"{avg_humidity:.1f}%")
                    else:
                        st.metric("Avg Humidity", "N/A")
                
                with col3:
                    if 'pressure' in weather_df.columns:
                        avg_pressure = weather_df['pressure'].mean()
                        st.metric("Avg Pressure", f"{avg_pressure:.1f} hPa")
                    else:
                        st.metric("Avg Pressure", "N/A")
                
                with col4:
                    st.metric("Data Points", len(weather_df))
                
                # Show weather data table
                st.markdown(f"""
                <div class='data-card'>
                    <h4 style='color: {COLOR_THEORY["text_dark"]}; margin-bottom: 15px;'>Weather Data Table</h4>
                </div>
                """, unsafe_allow_html=True)
                
                weather_cols = [col for col in ['temperature', 'humidity', 'pressure', 'condition', 'city'] 
                              if col in weather_df.columns]
                if weather_cols:
                    st.dataframe(weather_df[weather_cols].head(6), use_container_width=True)
                    
        except Exception as e:
            st.error(f"Error displaying weather data: {str(e)}")

def show_analytics():
    """Analytics page"""
    st.markdown(f"<div class='section-header'>📊 Data Analytics</div>", 
               unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"<div class='subsection-header'>📈 Earthquake Statistics</div>", 
                   unsafe_allow_html=True)
        
        if st.session_state.earthquake_data:
            try:
                eq_df = pd.DataFrame(st.session_state.earthquake_data)
                
                if not eq_df.empty and 'magnitude' in eq_df.columns:
                    stats_data = {
                        'Max Magnitude': eq_df['magnitude'].max(),
                        'Min Magnitude': eq_df['magnitude'].min(),
                        'Average Magnitude': eq_df['magnitude'].mean(),
                        'Total Earthquakes': len(eq_df)
                    }
                    
                    for stat, value in stats_data.items():
                        if 'Magnitude' in stat:
                            st.metric(stat, f"{value:.2f}")
                        else:
                            st.metric(stat, value)
                else:
                    st.info("No magnitude data available for statistics")
                    
            except Exception as e:
                st.error(f"Error calculating statistics: {str(e)}")
    
    with col2:
        st.markdown(f"<div class='subsection-header'>🌡️ Weather Statistics</div>", 
                   unsafe_allow_html=True)
        
        if st.session_state.weather_data:
            try:
                weather_df = pd.DataFrame(st.session_state.weather_data)
                
                if not weather_df.empty:
                    if 'temperature' in weather_df.columns:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Max Temp", f"{weather_df['temperature'].max():.1f}°C")
                        with col2:
                            st.metric("Min Temp", f"{weather_df['temperature'].min():.1f}°C")
            except Exception as e:
                st.error(f"Error calculating weather statistics: {str(e)}")

def show_raw_data():
    """Raw data tables page"""
    st.markdown(f"<div class='section-header'>📋 Raw Data Explorer</div>", 
               unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🌋 Earthquakes", "⚠️ Alerts", "🌤️ Weather"])
    
    with tab1:
        st.markdown(f"<div class='subsection-header'>Earthquake Data</div>", 
                   unsafe_allow_html=True)
        
        if st.session_state.earthquake_data:
            try:
                eq_df = pd.DataFrame(st.session_state.earthquake_data)
                st.dataframe(eq_df, use_container_width=True)
                
                st.markdown(f"<div class='subsection-header'>Data Summary</div>", 
                           unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Records", len(eq_df))
                with col2:
                    if 'magnitude' in eq_df.columns:
                        st.metric("Max Magnitude", f"{eq_df['magnitude'].max():.1f}")
                with col3:
                    if 'depth' in eq_df.columns:
                        st.metric("Average Depth", f"{eq_df['depth'].mean():.1f} km")
                        
            except Exception as e:
                st.error(f"Error displaying earthquake data: {str(e)}")
    
    with tab2:
        st.markdown(f"<div class='subsection-header'>Weather Alerts</div>", 
                   unsafe_allow_html=True)
        
        if st.session_state.severe_alerts:
            try:
                alerts_df = pd.DataFrame(st.session_state.severe_alerts)
                st.dataframe(alerts_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying alert data: {str(e)}")
    
    with tab3:
        st.markdown(f"<div class='subsection-header'>Weather Data</div>", 
                   unsafe_allow_html=True)
        
        if st.session_state.weather_data:
            try:
                weather_df = pd.DataFrame(st.session_state.weather_data)
                st.dataframe(weather_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying weather data: {str(e)}")

if __name__ == "__main__":
    main()
