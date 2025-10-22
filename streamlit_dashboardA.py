import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
import numpy as np
import math

# Page configuration
st.set_page_config(
    page_title="GeoWeather Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Advanced Color Theory Palette - Earth & Sky inspired
COLOR_THEORY = {
    # Primary Earth Tones
    "earth_green": "#2E8B57",      # Sea Green - stability, growth
    "deep_blue": "#1E6FA9",        # Trust, calmness
    "warm_amber": "#FF8C42",       # Energy, alerts
    "rich_clay": "#D35400",        # Strength, earthquakes
    
    # Secondary Nature Palette
    "forest_green": "#228B22",     # Nature, safety
    "sky_blue": "#4682B4",         # Openness, weather
    "sunset_orange": "#FF6B35",    # Warning, attention
    "storm_gray": "#2C3E50",       # Depth, data
    
    # Background & UI
    "cream_white": "#FDF6E3",      # Warm background
    "card_white": "#FFFFFF",       # Clean cards
    "text_dark": "#2C3E50",        # Readable text
    "text_light": "#7F8C8D"        # Secondary text
}

# Custom CSS with advanced styling
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    * {{
        font-family: 'Inter', sans-serif;
    }}
    
    .main {{
        background: linear-gradient(135deg, {COLOR_THEORY['cream_white']}, #E8F4F8);
    }}
    
    .stApp {{
        background: linear-gradient(135deg, {COLOR_THEORY['cream_white']}, #E8F4F8);
    }}
    
    .earth-kpi {{
        background: linear-gradient(135deg, {COLOR_THEORY['earth_green']}, {COLOR_THEORY['forest_green']});
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(46, 139, 87, 0.3);
        margin: 10px;
        border: none;
    }}
    
    .weather-kpi {{
        background: linear-gradient(135deg, {COLOR_THEORY['deep_blue']}, {COLOR_THEORY['sky_blue']});
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(30, 111, 169, 0.3);
        margin: 10px;
        border: none;
    }}
    
    .alert-kpi {{
        background: linear-gradient(135deg, {COLOR_THEORY['warm_amber']}, {COLOR_THEORY['rich_clay']});
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(255, 107, 53, 0.3);
        margin: 10px;
        border: none;
    }}
    
    .data-card {{
        background: {COLOR_THEORY['card_white']};
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 6px 15px rgba(44, 62, 80, 0.1);
        margin: 15px 0;
        border-left: 5px solid {COLOR_THEORY['earth_green']};
        transition: transform 0.3s ease;
    }}
    
    .data-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 12px 25px rgba(44, 62, 80, 0.15);
    }}
    
    .alert-card {{
        border-left: 5px solid {COLOR_THEORY['warm_amber']};
        background: linear-gradient(90deg, #FFF9F5, {COLOR_THEORY['card_white']});
    }}
    
    .section-header {{
        color: {COLOR_THEORY['storm_gray']};
        border-bottom: 3px solid {COLOR_THEORY['earth_green']};
        padding-bottom: 12px;
        margin: 30px 0 20px 0;
        font-weight: 700;
        font-size: 1.8rem;
    }}
    
    .metric-value {{
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        margin: 10px 0 !important;
    }}
    
    .sidebar .sidebar-content {{
        background: linear-gradient(180deg, {COLOR_THEORY['storm_gray']}, {COLOR_THEORY['deep_blue']});
        color: white;
    }}
</style>
""", unsafe_allow_html=True)

class GeoWeatherIntelligence:
    def __init__(self):
        self.base_url = "https://panditadata.com"
        
    def get_city_coordinates(self, city_name):
        """Get latitude and longitude for a city"""
        try:
            response = requests.get(f"{self.base_url}/weather/{city_name}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('lat'), data.get('lon')
            return None, None
        except Exception as e:
            st.error(f"Error fetching coordinates: {e}")
            return None, None
    
    def get_earthquake_data(self):
        """Get earthquake data"""
        try:
            response = requests.get(f"{self.base_url}/earthquakesd", timeout=10)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            st.error(f"Error fetching earthquake data: {e}")
            return []
    
    def get_severe_alerts(self):
        """Get severe weather alerts"""
        try:
            response = requests.get(f"{self.base_url}/api/severe_alerts", timeout=10)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            st.error(f"Error fetching severe alerts: {e}")
            return []
    
    def get_weather_data(self):
        """Get general weather data"""
        try:
            response = requests.get(f"{self.base_url}/weather_data", timeout=10)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            st.error(f"Error fetching weather data: {e}")
            return []

def create_custom_chart(chart_type, data, title, colors):
    """Create custom matplotlib charts with enhanced styling"""
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=COLOR_THEORY['card_white'])
    
    # Set style
    ax.set_facecolor(COLOR_THEORY['card_white'])
    fig.patch.set_facecolor(COLOR_THEORY['card_white'])
    
    if chart_type == "bar":
        bars = ax.bar(range(len(data)), list(data.values()), 
                     color=colors, alpha=0.8, edgecolor=COLOR_THEORY['storm_gray'], linewidth=1)
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(list(data.keys()), rotation=45)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
    
    elif chart_type == "line":
        ax.plot(list(data.keys()), list(data.values()), 
               color=colors[0], linewidth=3, marker='o', markersize=8)
        ax.fill_between(list(data.keys()), list(data.values()), 
                       alpha=0.3, color=colors[0])
    
    elif chart_type == "pie":
        wedges, texts, autotexts = ax.pie(data.values(), labels=data.keys(), 
                                         autopct='%1.1f%%', colors=colors,
                                         startangle=90, shadow=True)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
    
    # Styling
    ax.set_title(title, fontsize=16, fontweight='bold', 
                color=COLOR_THEORY['storm_gray'], pad=20)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(COLOR_THEORY['text_light'])
    ax.spines['bottom'].set_color(COLOR_THEORY['text_light'])
    ax.tick_params(colors=COLOR_THEORY['text_light'])
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    return fig

def create_2d_earthquake_map(earthquakes, center_lat, center_lon, city_name):
    """Create a 2D earthquake map visualization"""
    if not earthquakes:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 8), facecolor=COLOR_THEORY['card_white'])
    fig.patch.set_facecolor(COLOR_THEORY['card_white'])
    ax.set_facecolor('#E8F4F8')
    
    # Plot earthquakes
    lats, lons, mags = [], [], []
    for eq in earthquakes[:50]:  # Limit to 50 for clarity
        if 'lat' in eq and 'lon' in eq and 'magnitude' in eq:
            lats.append(float(eq['lat']))
            lons.append(float(eq['lon']))
            mags.append(float(eq['magnitude']))
    
    if not lats:
        return None
    
    # Create scatter plot with size based on magnitude
    scatter = ax.scatter(lons, lats, s=[m*20 for m in mags], 
                        c=mags, cmap='YlOrRd', alpha=0.7, 
                        edgecolors=COLOR_THEORY['storm_gray'], linewidth=1)
    
    # Add city center
    ax.scatter([center_lon], [center_lat], color=COLOR_THEORY['deep_blue'], 
              s=200, marker='*', edgecolor='white', linewidth=2, 
              label=f'Center: {city_name}')
    
    # Add labels for major earthquakes
    for i, (lat, lon, mag) in enumerate(zip(lats, lons, mags)):
        if mag > 5.0:  # Label only major earthquakes
            ax.annotate(f'M{mag}', (lon, lat), xytext=(5, 5), 
                       textcoords='offset points', fontweight='bold',
                       color=COLOR_THEORY['rich_clay'])
    
    # Styling
    ax.set_title(f'Earthquake Distribution - {city_name}', 
                fontsize=18, fontweight='bold', color=COLOR_THEORY['storm_gray'], pad=20)
    ax.set_xlabel('Longitude', fontweight='bold', color=COLOR_THEORY['text_light'])
    ax.set_ylabel('Latitude', fontweight='bold', color=COLOR_THEORY['text_light'])
    ax.legend()
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Magnitude', fontweight='bold', color=COLOR_THEORY['text_light'])
    
    plt.tight_layout()
    return fig

def main():
    # Initialize dashboard
    dashboard = GeoWeatherIntelligence()
    
    # Sidebar with enhanced design
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='color: white; margin: 0;'>🌍</h1>
            <h2 style='color: white; margin: 10px 0;'>GeoWeather Intelligence</h2>
            <p style='color: #BDC3C7;'>Real-time Earth & Weather Analytics</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # City input with styling
        st.markdown("<h3 style='color: white;'>📍 Location Setup</h3>", unsafe_allow_html=True)
        city_name = st.text_input("Enter City Name", "London", key="city_input")
        
        if st.button("🚀 Get GeoWeather Data", use_container_width=True, type="primary"):
            with st.spinner("🛰️ Scanning satellite data..."):
                lat, lon = dashboard.get_city_coordinates(city_name)
                if lat and lon:
                    st.session_state.update({
                        'city_name': city_name,
                        'lat': lat,
                        'lon': lon,
                        'earthquake_data': dashboard.get_earthquake_data(),
                        'severe_alerts': dashboard.get_severe_alerts(),
                        'weather_data': dashboard.get_weather_data(),
                        'data_loaded': True
                    })
                    st.success("✅ Data loaded successfully!")
                else:
                    st.error("❌ Could not find coordinates for the specified city")
        
        st.markdown("---")
        
        # Navigation
        st.markdown("<h3 style='color: white;'>🧭 Navigation</h3>", unsafe_allow_html=True)
        page = st.radio("Select View", 
                       ["📊 Overview Dashboard", "📈 Analytics & Charts", "📋 Raw Data Explorer"],
                       label_visibility="collapsed")
        
        st.markdown("---")
        st.markdown("""
        <div style='color: #BDC3C7; font-size: 0.8rem;'>
        <p><strong>🌐 Data Sources:</strong></p>
        <ul>
            <li>Seismic Activity API</li>
            <li>Weather Intelligence</li>
            <li>Alert Systems</li>
        </ul>
        <p style='margin-top: 20px;'>Real-time monitoring & analytics</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content
    if 'data_loaded' not in st.session_state:
        show_landing_page()
    else:
        if "Overview Dashboard" in page:
            show_overview_dashboard(dashboard)
        elif "Analytics & Charts" in page:
            show_analytics_dashboard(dashboard)
        else:
            show_raw_data_explorer(dashboard)

def show_landing_page():
    """Show landing page before data is loaded"""
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 60px 20px;'>
            <h1 style='color: #2C3E50; font-size: 3rem; margin-bottom: 20px;'>🌍 GeoWeather Intelligence</h1>
            <p style='color: #7F8C8D; font-size: 1.2rem; margin-bottom: 40px;'>
            Advanced Earth Observation & Weather Analytics Platform
            </p>
            <div style='background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1);'>
                <h3 style='color: #2E8B57;'>🚀 Get Started</h3>
                <p>Enter a city name in the sidebar and click <strong>Get GeoWeather Data</strong> to begin your analysis.</p>
                <div style='display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-top: 30px;'>
                    <div style='padding: 15px; background: #E8F5E8; border-radius: 10px;'>
                        <h4 style='color: #2E8B57;'>🌋 Seismic Data</h4>
                        <p>Earthquake monitoring & analysis</p>
                    </div>
                    <div style='padding: 15px; background: #E8F4F8; border-radius: 10px;'>
                        <h4 style='color: #1E6FA9;'>⛈️ Weather Intelligence</h4>
                        <p>Real-time weather patterns</p>
                    </div>
                    <div style='padding: 15px; background: #FFF5E8; border-radius: 10px;'>
                        <h4 style='color: #FF8C42;'>⚠️ Alert Systems</h4>
                        <p>Early warning systems</p>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_overview_dashboard(dashboard):
    """Show main overview dashboard"""
    city_name = st.session_state.city_name
    lat = st.session_state.lat
    lon = st.session_state.lon
    
    st.markdown(f"<h1 class='section-header'>🌐 Earth Intelligence - {city_name}</h1>", unsafe_allow_html=True)
    
    # Location Overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class='earth-kpi'>
            <h3>📍 Target Location</h3>
            <div class='metric-value'>{city_name}</div>
            <p>Analysis Center</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='weather-kpi'>
            <h3>🌐 Coordinates</h3>
            <div class='metric-value'>{lat:.4f}, {lon:.4f}</div>
            <p>Latitude, Longitude</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        earthquakes = st.session_state.earthquake_data
        recent_count = len(earthquakes) if earthquakes else 0
        st.markdown(f"""
        <div class='earth-kpi'>
            <h3>🌋 Seismic Events</h3>
            <div class='metric-value'>{recent_count}</div>
            <p>Total Recorded</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        alerts = st.session_state.severe_alerts
        alert_count = len(alerts) if alerts else 0
        st.markdown(f"""
        <div class='alert-kpi'>
            <h3>⚠️ Active Alerts</h3>
            <div class='metric-value'>{alert_count}</div>
            <p>Weather Warnings</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 2D Earthquake Map
    st.markdown("<h2 class='section-header'>🗺️ Seismic Activity Map</h2>", unsafe_allow_html=True)
    
    if st.session_state.earthquake_data:
        fig = create_2d_earthquake_map(
            st.session_state.earthquake_data, 
            st.session_state.lat, 
            st.session_state.lon,
            st.session_state.city_name
        )
        if fig:
            st.pyplot(fig)
        else:
            st.info("No earthquake data available for mapping")
    else:
        st.info("Loading earthquake data...")
    
    # Quick Stats & Alerts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3 style='color: #2C3E50;'>📈 Quick Statistics</h3>", unsafe_allow_html=True)
        
        if st.session_state.earthquake_data:
            eq_data = st.session_state.earthquake_data
            magnitudes = [eq.get('magnitude', 0) for eq in eq_data if eq.get('magnitude')]
            if magnitudes:
                stats_data = {
                    'Max Magnitude': max(magnitudes),
                    'Avg Magnitude': sum(magnitudes) / len(magnitudes),
                    'Min Magnitude': min(magnitudes),
                    'Total Events': len(magnitudes)
                }
                
                fig = create_custom_chart("bar", stats_data, "Earthquake Statistics", 
                                        [COLOR_THEORY['earth_green'], COLOR_THEORY['deep_blue'], 
                                         COLOR_THEORY['warm_amber'], COLOR_THEORY['rich_clay']])
                st.pyplot(fig)
    
    with col2:
        st.markdown("<h3 style='color: #2C3E50;'>🚨 Recent Alerts</h3>", unsafe_allow_html=True)
        
        alerts = st.session_state.severe_alerts
        if alerts:
            for i, alert in enumerate(alerts[:4]):
                alert_type = alert.get('type', 'Unknown Alert')
                severity = alert.get('severity', 'Medium')
                description = alert.get('description', 'No description available')
                
                st.markdown(f"""
                <div class='data-card alert-card'>
                    <div style='display: flex; align-items: center; margin-bottom: 10px;'>
                        <span style='background: {COLOR_THEORY['warm_amber']}; color: white; padding: 5px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: bold;'>
                            {severity}
                        </span>
                        <span style='margin-left: 10px; font-weight: bold; color: {COLOR_THEORY['storm_gray']};'>
                            {alert_type}
                        </span>
                    </div>
                    <p style='color: {COLOR_THEORY['text_light']}; margin: 0;'>{description}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='data-card'>
                <p style='text-align: center; color: {COLOR_THEORY['text_light']};'>
                    ✅ No active alerts in this region
                </p>
            </div>
            """, unsafe_allow_html=True)

def show_analytics_dashboard(dashboard):
    """Show advanced analytics and charts"""
    st.markdown("<h1 class='section-header'>📊 Advanced Analytics</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Earthquake Magnitude Distribution
        if st.session_state.earthquake_data:
            magnitudes = [eq.get('magnitude', 0) for eq in st.session_state.earthquake_data if eq.get('magnitude')]
            if magnitudes:
                mag_ranges = {'0-2': 0, '2-4': 0, '4-6': 0, '6+': 0}
                for mag in magnitudes:
                    if mag < 2: mag_ranges['0-2'] += 1
                    elif mag < 4: mag_ranges['2-4'] += 1
                    elif mag < 6: mag_ranges['4-6'] += 1
                    else: mag_ranges['6+'] += 1
                
                fig = create_custom_chart("pie", mag_ranges, "Earthquake Magnitude Distribution",
                                        [COLOR_THEORY['sky_blue'], COLOR_THEORY['earth_green'], 
                                         COLOR_THEORY['warm_amber'], COLOR_THEORY['rich_clay']])
                st.pyplot(fig)
    
    with col2:
        # Weather Data Analysis
        if st.session_state.weather_data:
            weather_df = pd.DataFrame(st.session_state.weather_data)
            if not weather_df.empty and 'temperature' in weather_df.columns:
                temp_data = weather_df['temperature'].value_counts().head(10)
                if not temp_data.empty:
                    fig = create_custom_chart("bar", temp_data, "Temperature Frequency",
                                            [COLOR_THEORY['deep_blue']] * len(temp_data))
                    st.pyplot(fig)
    
    # Additional Analytics
    st.markdown("<h2 class='section-header'>📈 Trend Analysis</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Time-based analysis (simulated)
        time_data = {
            'Jan': 45, 'Feb': 52, 'Mar': 48, 'Apr': 55,
            'May': 60, 'Jun': 65, 'Jul': 62, 'Aug': 58
        }
        fig = create_custom_chart("line", time_data, "Monthly Activity Trend",
                                [COLOR_THEORY['earth_green']])
        st.pyplot(fig)
    
    with col2:
        # Alert type distribution
        if st.session_state.severe_alerts:
            alert_types = {}
            for alert in st.session_state.severe_alerts:
                alert_type = alert.get('type', 'Unknown')
                alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
            
            if alert_types:
                fig = create_custom_chart("bar", alert_types, "Alert Type Distribution",
                                        [COLOR_THEORY['warm_amber'], COLOR_THEORY['rich_clay'], 
                                         COLOR_THEORY['sunset_orange']])
                st.pyplot(fig)

def show_raw_data_explorer(dashboard):
    """Show raw data explorer with tables"""
    st.markdown("<h1 class='section-header'>📋 Raw Data Explorer</h1>", unsafe_allow_html=True)
    
    # Create tabs for different data types
    tab1, tab2, tab3 = st.tabs(["🌋 Earthquake Data", "⚠️ Alert Data", "🌤️ Weather Data"])
    
    with tab1:
        st.markdown("<h3 style='color: #2C3E50;'>Seismic Activity Data</h3>", unsafe_allow_html=True)
        if st.session_state.earthquake_data:
            eq_df = pd.DataFrame(st.session_state.earthquake_data)
            # Select only relevant columns for display
            display_columns = [col for col in ['location', 'magnitude', 'depth', 'lat', 'lon', 'time'] 
                             if col in eq_df.columns]
            if display_columns:
                st.dataframe(eq_df[display_columns].head(20), use_container_width=True)
                
                # Show basic statistics
                st.markdown("#### 📊 Data Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Records", len(eq_df))
                with col2:
                    if 'magnitude' in eq_df.columns:
                        st.metric("Average Magnitude", f"{eq_df['magnitude'].mean():.2f}")
                with col3:
                    if 'depth' in eq_df.columns:
                        st.metric("Max Depth", f"{eq_df['depth'].max():.1f} km")
        else:
            st.info("No earthquake data available")
    
    with tab2:
        st.markdown("<h3 style='color: #2C3E50;'>Weather Alert Data</h3>", unsafe_allow_html=True)
        if st.session_state.severe_alerts:
            alerts_df = pd.DataFrame(st.session_state.severe_alerts)
            st.dataframe(alerts_df.head(20), use_container_width=True)
            
            st.markdown("#### 🚨 Alert Overview")
            if 'severity' in alerts_df.columns:
                severity_counts = alerts_df['severity'].value_counts()
                for severity, count in severity_counts.items():
                    st.write(f"**{severity}**: {count} alerts")
        else:
            st.info("No alert data available")
    
    with tab3:
        st.markdown("<h3 style='color: #2C3E50;'>Weather Observation Data</h3>", unsafe_allow_html=True)
        if st.session_state.weather_data:
            weather_df = pd.DataFrame(st.session_state.weather_data)
            st.dataframe(weather_df.head(20), use_container_width=True)
            
            st.markdown("#### 🌡️ Weather Summary")
            if 'temperature' in weather_df.columns:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Avg Temp", f"{weather_df['temperature'].mean():.1f}°C")
                with col2:
                    st.metric("Min Temp", f"{weather_df['temperature'].min():.1f}°C")
                with col3:
                    st.metric("Max Temp", f"{weather_df['temperature'].max():.1f}°C")

if __name__ == "__main__":
    main()
