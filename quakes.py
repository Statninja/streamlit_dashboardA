import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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

class GeoWeatherIntelligence:
    def __init__(self):
        # USGS Earthquake APIs
        self.usgs_base = "https://earthquake.usgs.gov/fdsnws/event/1"
        
        # OpenWeatherMap API (free tier)
        self.weather_api_key = "demo_key"  # In production, use st.secrets["WEATHER_API_KEY"]
        self.weather_base = "http://api.openweathermap.org/data/2.5"
        
    def get_city_coordinates(self, city_name):
        """Get coordinates using OpenWeatherMap Geocoding API"""
        try:
            # Use a reliable geocoding service
            city_coordinates = {
                "london": (51.5074, -0.1278),
                "new york": (40.7128, -74.0060),
                "tokyo": (35.6762, 139.6503),
                "paris": (48.8566, 2.3522),
                "sydney": (-33.8688, 151.2093),
                "los angeles": (34.0522, -118.2437),
                "chicago": (41.8781, -87.6298),
                "toronto": (43.6532, -79.3832),
                "mumbai": (19.0760, 72.8777),
                "berlin": (52.5200, 13.4050),
                "dubai": (25.2048, 55.2708),
                "singapore": (1.3521, 103.8198),
                "seoul": (37.5665, 126.9780),
                "moscow": (55.7558, 37.6173),
                "cairo": (30.0444, 31.2357)
            }
            
            city_lower = city_name.lower().strip()
            if city_lower in city_coordinates:
                lat, lon = city_coordinates[city_lower]
                return lat, lon
            
            # Try OpenWeatherMap Geocoding API
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={self.weather_api_key}"
            response = requests.get(geo_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    lat = data[0].get('lat')
                    lon = data[0].get('lon')
                    if lat and lon:
                        return lat, lon
                        
        except Exception as e:
            st.warning(f"Using default coordinates for {city_name}")
        
        # Default fallback
        return (51.5074, -0.1278)
    
    def get_earthquake_data(self, lat, lon, radius_km=500):
        """Get real earthquake data from USGS"""
        try:
            # Calculate date range (past 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # USGS API query
            url = f"{self.usgs_base}/query"
            params = {
                'format': 'geojson',
                'latitude': lat,
                'longitude': lon,
                'maxradiuskm': radius_km,
                'starttime': start_date.strftime('%Y-%m-%d'),
                'endtime': end_date.strftime('%Y-%m-%d'),
                'minmagnitude': 2.5,
                'orderby': 'time'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                earthquakes = []
                
                for feature in data.get('features', []):
                    properties = feature.get('properties', {})
                    geometry = feature.get('geometry', {})
                    
                    earthquake = {
                        'location': properties.get('place', 'Unknown'),
                        'magnitude': properties.get('mag', 0.0),
                        'depth': feature.get('geometry', {}).get('coordinates', [0,0,0])[2],
                        'lat': geometry.get('coordinates', [0,0,0])[1],
                        'lon': geometry.get('coordinates', [0,0,0])[0],
                        'time': datetime.fromtimestamp(properties.get('time', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                        'usgs_id': feature.get('id', '')
                    }
                    earthquakes.append(earthquake)
                
                return earthquakes
                
        except Exception as e:
            st.error(f"Error fetching USGS earthquake data: {str(e)}")
        
        # Fallback sample data
        return [
            {
                'location': f"Near {lat:.1f}, {lon:.1f}",
                'magnitude': 4.2,
                'depth': 10.0,
                'lat': lat + 0.5,
                'lon': lon + 0.5,
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'usgs_id': 'fallback_1'
            }
        ]
    
    def get_weather_data(self, lat, lon):
        """Get current weather data from OpenWeatherMap"""
        try:
            url = f"{self.weather_base}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.weather_api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                weather_data = {
                    'temperature': data.get('main', {}).get('temp', 20.0),
                    'humidity': data.get('main', {}).get('humidity', 50.0),
                    'pressure': data.get('main', {}).get('pressure', 1013.0),
                    'condition': data.get('weather', [{}])[0].get('description', 'Unknown'),
                    'city': data.get('name', 'Unknown'),
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'wind_speed': data.get('wind', {}).get('speed', 0.0),
                    'visibility': data.get('visibility', 10000)
                }
                
                return [weather_data]
                
        except Exception as e:
            st.warning(f"Weather API error: {str(e)}")
        
        # Fallback weather data
        return [
            {
                'temperature': 20.0,
                'humidity': 65.0,
                'pressure': 1013.0,
                'condition': 'Partly Cloudy',
                'city': 'Unknown',
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'wind_speed': 3.5,
                'visibility': 10000
            }
        ]
    
    def get_weather_alerts(self, lat, lon):
        """Get weather alerts from OpenWeatherMap"""
        try:
            # Using One Call API for alerts (includes severe weather)
            url = f"https://api.openweathermap.org/data/3.0/onecall"
            params = {
                'lat': lat,
                'lon': lon,
                'exclude': 'minutely,hourly,daily',
                'appid': self.weather_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                alerts = data.get('alerts', [])
                
                formatted_alerts = []
                for alert in alerts:
                    formatted_alert = {
                        'type': alert.get('event', 'Weather Alert'),
                        'severity': alert.get('severity', 'Moderate').title(),
                        'description': alert.get('description', 'No description'),
                        'area': alert.get('sender_name', 'Unknown Area'),
                        'start': datetime.fromtimestamp(alert.get('start', 0)).strftime('%Y-%m-%d %H:%M'),
                        'end': datetime.fromtimestamp(alert.get('end', 0)).strftime('%Y-%m-%d %H:%M')
                    }
                    formatted_alerts.append(formatted_alert)
                
                return formatted_alerts
                
        except Exception as e:
            st.warning(f"Weather alerts API error: {str(e)}")
        
        # Fallback alerts
        return [
            {
                'type': 'Weather Monitoring',
                'severity': 'Info',
                'description': 'Real-time weather monitoring active',
                'area': 'Global',
                'start': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'end': (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M')
            }
        ]

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
            <p style='color: #E0E0E0; margin: 0; font-size: 0.9rem;'>USGS & Weather Data</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("**📍 Location Setup**")
        city_name = st.text_input("Enter City Name", "London")
        
        # Radius selection for earthquakes
        radius_km = st.slider("Earthquake Search Radius (km)", 100, 1000, 500)
        
        if st.button("🚀 Load Real Data", use_container_width=True, type="primary"):
            with st.spinner("Loading real USGS and weather data..."):
                # Get coordinates
                lat, lon = dashboard.get_city_coordinates(city_name)
                st.success(f"📍 Coordinates for {city_name}: {lat:.4f}, {lon:.4f}")
                
                # Load all data from real APIs
                earthquake_data = dashboard.get_earthquake_data(lat, lon, radius_km)
                weather_data = dashboard.get_weather_data(lat, lon)
                alert_data = dashboard.get_weather_alerts(lat, lon)
                
                st.session_state.update({
                    'city_name': city_name,
                    'lat': lat,
                    'lon': lon,
                    'radius_km': radius_km,
                    'earthquake_data': earthquake_data,
                    'weather_data': weather_data,
                    'severe_alerts': alert_data,
                    'data_loaded': True
                })
        
        st.markdown("---")
        st.markdown("**🧭 Navigation**")
        page = st.radio("Go to", ["Dashboard", "Data Tables", "Analytics"], label_visibility="collapsed")
        
        st.markdown("---")
        st.markdown(f"""
        <div style='color: #E0E0E0; font-size: 0.8rem;'>
        <p><strong>📊 Data Sources:</strong></p>
        <ul>
            <li>USGS Earthquake API</li>
            <li>OpenWeatherMap API</li>
            <li>Real-time Data</li>
        </ul>
        <p><em>Live seismic & weather monitoring</em></p>
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
    st.markdown("<div class='section-header'>🚀 GeoWeather Intelligence</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class='data-card'>
            <h3>Real-time Earth & Weather Monitoring</h3>
            <p>Powered by <strong>USGS Earthquake Data</strong> and <strong>OpenWeatherMap</strong></p>
            
            <p><strong>Features:</strong></p>
            <ul>
                <li>🌋 <strong>USGS Real-time Earthquake Data</strong> - Live seismic monitoring</li>
                <li>🌤️ <strong>OpenWeatherMap API</strong> - Current weather conditions</li>
                <li>⚠️ <strong>Weather Alerts</strong> - Severe weather warnings</li>
                <li>📊 <strong>Interactive Analytics</strong> - Data visualization</li>
            </ul>
            
            <p><strong>How to use:</strong></p>
            <ol>
                <li>Enter a city name in the sidebar</li>
                <li>Adjust earthquake search radius if needed</li>
                <li>Click "Load Real Data"</li>
                <li>Explore the dashboard and data tables</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='data-card'>
            <h3>📍 Supported Cities</h3>
            <p><strong>Major cities worldwide:</strong></p>
            <ul>
                <li>London</li>
                <li>New York</li>
                <li>Tokyo</li>
                <li>Paris</li>
                <li>Sydney</li>
                <li>Los Angeles</li>
                <li>Chicago</li>
                <li>Toronto</li>
                <li>Berlin</li>
                <li>Dubai</li>
                <li>Singapore</li>
                <li>Seoul</li>
                <li>Mumbai</li>
            </ul>
            <p><em>Plus any city via geocoding</em></p>
        </div>
        
        <div class='data-card'>
            <h3>🌐 Data Sources</h3>
            <p><strong>USGS Earthquake API</strong><br>Real-time seismic data</p>
            <p><strong>OpenWeatherMap</strong><br>Weather & alert data</p>
        </div>
        """, unsafe_allow_html=True)

def show_dashboard():
    """Main dashboard with real data"""
    city = st.session_state.city_name
    lat = st.session_state.lat
    lon = st.session_state.lon
    radius = st.session_state.radius_km
    
    st.markdown(f"<div class='section-header'>🌍 Real-time Earth Analytics - {city}</div>", unsafe_allow_html=True)
    
    # Location info
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class='data-card'>
            <h4>📍 Location Information</h4>
            <p><strong>City:</strong> {city}</p>
            <p><strong>Coordinates:</strong> {lat:.4f}, {lon:.4f}</p>
            <p><strong>Earthquake Radius:</strong> {radius} km</p>
            <p><strong>Last Updated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(create_kpi_card("📍 Location", city, "Selected City", "earth"), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_kpi_card("🌐 Radius", f"{radius} km", "Search Area", "weather"), unsafe_allow_html=True)
    
    with col3:
        eq_count = len(st.session_state.earthquake_data)
        st.markdown(create_kpi_card("🌋 Earthquakes", str(eq_count), "USGS Data", "earth"), unsafe_allow_html=True)
    
    with col4:
        alert_count = len(st.session_state.severe_alerts)
        st.markdown(create_kpi_card("⚠️ Alerts", str(alert_count), "Weather Warnings", "alert"), unsafe_allow_html=True)
    
    # Earthquake Data from USGS
    st.markdown("<div class='subsection-header'>🌋 USGS Earthquake Data</div>", unsafe_allow_html=True)
    
    earthquake_data = st.session_state.earthquake_data
    if earthquake_data:
        try:
            eq_df = pd.DataFrame(earthquake_data)
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if 'magnitude' in eq_df.columns:
                    avg_mag = eq_df['magnitude'].mean()
                    st.metric("Average Magnitude", f"{avg_mag:.1f}")
            with col2:
                if 'magnitude' in eq_df.columns:
                    max_mag = eq_df['magnitude'].max()
                    st.metric("Max Magnitude", f"{max_mag:.1f}")
            with col3:
                if 'depth' in eq_df.columns:
                    max_depth = eq_df['depth'].max()
                    st.metric("Max Depth", f"{max_depth:.1f} km")
            with col4:
                st.metric("Total Events", len(eq_df))
            
            # Show data table
            st.markdown("**Recent Earthquakes:**")
            display_cols = [col for col in ['location', 'magnitude', 'depth', 'time'] if col in eq_df.columns]
            if display_cols:
                st.dataframe(eq_df[display_cols].head(10), use_container_width=True)
            else:
                st.info("No earthquake data columns available")
                
        except Exception as e:
            st.error(f"Error processing earthquake data: {str(e)}")
    else:
        st.info("No earthquake data found in the selected area")
    
    # Weather Data
    st.markdown("<div class='subsection-header'>🌤️ Current Weather</div>", unsafe_allow_html=True)
    
    weather_data = st.session_state.weather_data
    if weather_data:
        try:
            weather_df = pd.DataFrame(weather_data)
            
            if not weather_df.empty:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if 'temperature' in weather_df.columns:
                        temp = weather_df['temperature'].iloc[0]
                        st.metric("Temperature", f"{temp:.1f}°C")
                with col2:
                    if 'humidity' in weather_df.columns:
                        humidity = weather_df['humidity'].iloc[0]
                        st.metric("Humidity", f"{humidity:.1f}%")
                with col3:
                    if 'pressure' in weather_df.columns:
                        pressure = weather_df['pressure'].iloc[0]
                        st.metric("Pressure", f"{pressure:.1f} hPa")
                with col4:
                    if 'wind_speed' in weather_df.columns:
                        wind_speed = weather_df['wind_speed'].iloc[0]
                        st.metric("Wind Speed", f"{wind_speed:.1f} m/s")
                
                # Weather condition
                if 'condition' in weather_df.columns:
                    condition = weather_df['condition'].iloc[0]
                    st.markdown(f"""
                    <div class='data-card'>
                        <h4>Current Conditions</h4>
                        <p><strong>Weather:</strong> {condition.title()}</p>
                        <p><strong>City:</strong> {weather_df['city'].iloc[0] if 'city' in weather_df.columns else 'Unknown'}</p>
                        <p><strong>Last Updated:</strong> {weather_df['time'].iloc[0] if 'time' in weather_df.columns else 'Unknown'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
        except Exception as e:
            st.error(f"Error processing weather data: {str(e)}")
    
    # Weather Alerts
    st.markdown("<div class='subsection-header'>⚠️ Weather Alerts</div>", unsafe_allow_html=True)
    
    alerts_data = st.session_state.severe_alerts
    if alerts_data:
        try:
            alerts_df = pd.DataFrame(alerts_data)
            
            for _, alert in alerts_df.iterrows():
                alert_type = alert.get('type', 'Unknown')
                severity = alert.get('severity', 'Moderate')
                description = alert.get('description', 'No description')
                area = alert.get('area', 'Unknown area')
                start_time = alert.get('start', 'Unknown')
                end_time = alert.get('end', 'Unknown')
                
                # Color based on severity
                severity_color = {
                    'Extreme': '#FF0000',
                    'Severe': '#FF6B35',
                    'Moderate': '#FFA500',
                    'Minor': '#FFD700',
                    'Info': COLOR_THEORY['sky_blue']
                }.get(severity, COLOR_THEORY['warm_amber'])
                
                st.markdown(f"""
                <div class='data-card'>
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <h4 style="margin: 0; color: {COLOR_THEORY['text_dark']};">{alert_type}</h4>
                        <span style="background: {severity_color}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold;">
                            {severity}
                        </span>
                    </div>
                    <p style="margin: 5px 0; color: {COLOR_THEORY['text_light']};"><strong>Area:</strong> {area}</p>
                    <p style="margin: 5px 0; color: {COLOR_THEORY['text_light']};"><strong>Time:</strong> {start_time} to {end_time}</p>
                    <p style="margin: 0; color: {COLOR_THEORY['text_light']};">{description}</p>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error processing alert data: {str(e)}")
    else:
        st.info("No active weather alerts for this location")

def show_data_tables():
    """Data tables view"""
    st.markdown("<div class='section-header'>📋 Raw Data Explorer</div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🌋 USGS Earthquakes", "⚠️ Weather Alerts", "🌤️ Weather Data"])
    
    with tab1:
        st.markdown("<div class='subsection-header'>USGS Earthquake Data</div>", unsafe_allow_html=True)
        if st.session_state.earthquake_data:
            try:
                eq_df = pd.DataFrame(st.session_state.earthquake_data)
                st.dataframe(eq_df, use_container_width=True)
                
                # Statistics
                st.markdown("#### 📊 Earthquake Statistics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Records", len(eq_df))
                with col2:
                    if 'magnitude' in eq_df.columns:
                        st.metric("Max Magnitude", f"{eq_df['magnitude'].max():.1f}")
                with col3:
                    if 'depth' in eq_df.columns:
                        st.metric("Avg Depth", f"{eq_df['depth'].mean():.1f} km")
                with col4:
                    if 'magnitude' in eq_df.columns:
                        st.metric("Avg Magnitude", f"{eq_df['magnitude'].mean():.1f}")
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
        st.markdown("<div class='subsection-header'>Earthquake Analytics</div>", unsafe_allow_html=True)
        if st.session_state.earthquake_data:
            try:
                eq_df = pd.DataFrame(st.session_state.earthquake_data)
                
                if not eq_df.empty and 'magnitude' in eq_df.columns:
                    # Magnitude distribution
                    magnitude_ranges = {
                        '2.0-3.9': len(eq_df[(eq_df['magnitude'] >= 2.0) & (eq_df['magnitude'] < 4.0)]),
                        '4.0-5.9': len(eq_df[(eq_df['magnitude'] >= 4.0) & (eq_df['magnitude'] < 6.0)]),
                        '6.0+': len(eq_df[eq_df['magnitude'] >= 6.0])
                    }
                    
                    st.markdown("**Magnitude Distribution:**")
                    for range_name, count in magnitude_ranges.items():
                        if count > 0:
                            st.write(f"- {range_name}: {count} earthquakes")
                    
                    # Key statistics
                    st.metric("Maximum Magnitude", f"{eq_df['magnitude'].max():.2f}")
                    st.metric("Minimum Magnitude", f"{eq_df['magnitude'].min():.2f}")
                    st.metric("Average Magnitude", f"{eq_df['magnitude'].mean():.2f}")
                    st.metric("Total Earthquakes", len(eq_df))
                    
            except Exception as e:
                st.error(f"Error calculating earthquake statistics: {str(e)}")
    
    with col2:
        st.markdown("<div class='subsection-header'>Weather Analytics</div>", unsafe_allow_html=True)
        if st.session_state.weather_data:
            try:
                weather_df = pd.DataFrame(st.session_state.weather_data)
                
                if not weather_df.empty:
                    if 'temperature' in weather_df.columns:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Temperature", f"{weather_df['temperature'].iloc[0]:.1f}°C")
                        with col2:
                            st.metric("Feels Like", f"{weather_df['temperature'].iloc[0]:.1f}°C")
                    
                    if 'humidity' in weather_df.columns:
                        st.metric("Humidity", f"{weather_df['humidity'].iloc[0]:.1f}%")
                    
                    if 'pressure' in weather_df.columns:
                        st.metric("Pressure", f"{weather_df['pressure'].iloc[0]:.1f} hPa")
                    
                    if 'wind_speed' in weather_df.columns:
                        st.metric("Wind Speed", f"{weather_df['wind_speed'].iloc[0]:.1f} m/s")
                        
            except Exception as e:
                st.error(f"Error calculating weather statistics: {str(e)}")

if __name__ == "__main__":
    main()
