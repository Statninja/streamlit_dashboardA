import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Page config
st.set_page_config(page_title="GeoWeather Dashboard", page_icon="🌍", layout="wide")

# Color scheme
COLORS = {
    "primary": "#2E8B57",
    "secondary": "#4682B4", 
    "accent": "#FF6B35",
    "background": "#F5F5F5"
}

# Custom CSS
st.markdown(f"""
<style>
    .main {{ background-color: {COLORS['background']}; }}
    .kpi-card {{
        background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['secondary']});
        color: white; padding: 20px; border-radius: 10px; text-align: center;
    }}
    .card {{
        background: white; padding: 20px; border-radius: 10px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 10px;
        border-left: 4px solid {COLORS['primary']};
    }}
</style>
""", unsafe_allow_html=True)

class Dashboard:
    def __init__(self):
        self.base_url = "https://panditadata.com"
    
    def get_coords(self, city):
        try:
            response = requests.get(f"{self.base_url}/weather/{city}")
            return response.json().get('lat'), response.json().get('lon')
        except:
            return None, None
    
    def get_earthquakes(self):
        try:
            return requests.get(f"{self.base_url}/earthquakesd").json()
        except:
            return []
    
    def get_alerts(self):
        try:
            return requests.get(f"{self.base_url}/api/severe_alerts").json()
        except:
            return []
    
    def get_weather(self):
        try:
            return requests.get(f"{self.base_url}/weather_data").json()
        except:
            return []

def main():
    st.sidebar.title("🌍 GeoWeather Dashboard")
    city = st.sidebar.text_input("Enter City Name", "London")
    
    if st.sidebar.button("Get Data"):
        dashboard = Dashboard()
        lat, lon = dashboard.get_coords(city)
        if lat and lon:
            st.session_state.update({
                'city': city, 'lat': lat, 'lon': lon,
                'earthquakes': dashboard.get_earthquakes(),
                'alerts': dashboard.get_alerts(),
                'weather': dashboard.get_weather()
            })
    
    page = st.sidebar.radio("Navigation", ["Dashboard", "Raw Data"])
    
    if 'city' not in st.session_state:
        st.info("👈 Enter city name and click Get Data")
        return
    
    if page == "Dashboard":
        show_dashboard()
    else:
        show_tables()

def show_dashboard():
    city = st.session_state.city
    st.title(f"🌤️ Dashboard - {city}")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>Earthquakes</h3>
            <h2>{len(st.session_state.earthquakes)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗺️ Earthquake Map")
        if st.session_state.earthquakes:
            df = pd.DataFrame(st.session_state.earthquakes)
            fig = px.scatter_mapbox(df, lat="lat", lon="lon", size="magnitude", 
                                  color="magnitude", zoom=3)
            fig.update_layout(mapbox_style="open-street-map", height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("⚠️ Alerts")
        for alert in st.session_state.alerts[:5]:
            st.markdown(f"""
            <div class="card">
                <h4>🚨 {alert.get('type', 'Alert')}</h4>
                <p>{alert.get('description', 'No description')}</p>
            </div>
            """, unsafe_allow_html=True)

def show_tables():
    st.title("📋 Raw Data")
    
    tab1, tab2, tab3 = st.tabs(["Earthquakes", "Alerts", "Weather"])
    
    with tab1:
        if st.session_state.earthquakes:
            st.dataframe(pd.DataFrame(st.session_state.earthquakes))
    
    with tab2:
        if st.session_state.alerts:
            st.dataframe(pd.DataFrame(st.session_state.alerts))
    
    with tab3:
        if st.session_state.weather:
            st.dataframe(pd.DataFrame(st.session_state.weather))

if __name__ == "__main__":
    main()
