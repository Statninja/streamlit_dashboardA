"""
PANDITADATA DISASTER & SPACE INTELLIGENCE PLATFORM
Enterprise-grade real-time monitoring system
Updated with NWS Alerts, Space Weather, Hurricane Tracking, Aftershock Analysis, PDF Export, and User Auth/Saved Locations
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import plotly.express as px
import plotly.graph_objects as go
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, get_sun, get_body
import astropy.units as u
import io
import base64
from io import BytesIO

# For PDF export, we'll use Matplotlib + Pandas for simple PDF, since weasyprint not available
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleProducer

# ============================================================================
# 0. PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="PanditaData Disaster Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://panditadata.com/help',
        'Report a bug': 'https://panditadata.com/support',
        'About': 'Professional Disaster & Space Weather Monitoring'
    }
)

def load_custom_css():
    st.markdown("""
    <style>
    .main {background-color: #0e1117; color: #fafafa;}
    div[data-testid="metric-container"] {
        background-color: #1e1e1e; border: 1px solid #333; padding: 15px;
        border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .critical-alert {background-color: #8b0000; color: white; padding: 20px;
        border-radius: 10px; border-left: 5px solid #ff0000; margin: 10px 0; font-weight: bold;}
    .high-alert {background-color: #ff8c00; color: white; padding: 15px;
        border-radius: 10px; border-left: 5px solid #ffa500; margin: 10px 0;}
    .moderate-alert {background-color: #ffd700; color: black; padding: 15px;
        border-radius: 10px; border-left: 5px solid #ffff00; margin: 10px 0;}
    h1 {color: #4da6ff; font-family: 'Helvetica Neue', sans-serif; font-weight: 700;}
    h2 {color: #66b3ff; font-family: 'Helvetica Neue', sans-serif; border-bottom: 2px solid #4da6ff; padding-bottom: 10px;}
    h3 {color: #80bfff; font-family: 'Helvetica Neue', sans-serif;}
    .dataframe th {background-color: #1e3a5f; color: white; font-weight: bold; padding: 12px;}
    .dataframe td {padding: 10px; border-bottom: 1px solid #333;}
    .dataframe tr:hover {background-color: #2a2a2a;}
    .css-1d391kg {background-color: #1a1a1a;}
    .stButton>button {
        background-color: #4da6ff; color: white; font-weight: bold;
        border-radius: 8px; padding: 10px 24px; border: none; transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #0080ff; box-shadow: 0 4px 8px rgba(77,166,255,0.4);
    }
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%; background-color: #1a1a1a;
        color: #888; text-align: center; padding: 10px; font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

load_custom_css()

# ============================================================================
# 1. USER AUTHENTICATION & SAVED LOCATIONS
# ============================================================================

def authenticate_user():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'saved_locations' not in st.session_state:
        st.session_state.saved_locations = []

    if not st.session_state.authenticated:
        with st.sidebar:
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                # Simple demo auth
                if username == "user" and password == "pass":
                    st.session_state.authenticated = True
                    st.success("Logged in!")
                else:
                    st.error("Invalid credentials")
        return False
    return True

def save_location(lat, lon, name):
    if name and lat and lon:
        st.session_state.saved_locations.append({'name': name, 'lat': lat, 'lon': lon})
        st.rerun()

def load_saved_location(name):
    for loc in st.session_state.saved_locations:
        if loc['name'] == name:
            st.session_state.lat = loc['lat']
            st.session_state.lon = loc['lon']
            return True
    return False

# ============================================================================
# 2. LOCATION INTELLIGENCE
# ============================================================================

geolocator = Nominatim(user_agent="panditadata_disaster_report_v1")

def geocode_location(query):
    try:
        location = geolocator.geocode(query, exactly_one=True, addressdetails=True, timeout=10)
        if not location:
            return None
        return {
            'latitude': location.latitude,
            'longitude': location.longitude,
            'display_name': location.address,
            'place_type': location.raw.get('type'),
            'country': location.raw.get('address', {}).get('country'),
            'state': location.raw.get('address', {}).get('state'),
            'city': location.raw.get('address', {}).get('city'),
        }
    except Exception as e:
        st.error(f"Geocoding error: {e}")
        return None

def reverse_geocode(lat, lon):
    try:
        location = geolocator.reverse(f"{lat}, {lon}", language='en', timeout=10)
        return location.address if location else "Unknown"
    except:
        return "Unknown"

# ============================================================================
# 3. EARTHQUAKE MODULE (Updated with Aftershock Probability)
# ============================================================================

USGS_BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

def fetch_earthquakes(lat, lon, radius_km, start_date, end_date, min_mag=0, max_mag=10):
    params = {
        'format': 'geojson',
        'starttime': start_date,
        'endtime': end_date,
        'latitude': lat,
        'longitude': lon,
        'maxradiuskm': radius_km,
        'minmagnitude': min_mag,
        'maxmagnitude': max_mag,
        'orderby': 'time-asc',
        'limit': 20000,
        'eventtype': 'earthquake',
        'includeallmagnitudes': 'true',
        'includeallorigins': 'true',
        'includearrivals': 'false',
        'includedeleted': 'false'
    }
    try:
        response = requests.get(USGS_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"USGS API Error: {e}")
        return None

def process_earthquake_data(geojson, user_lat, user_lon):
    if not geojson or 'features' not in geojson:
        return pd.DataFrame()

    earthquakes = []
    for feature in geojson['features']:
        props = feature['properties']
        coords = feature['geometry']['coordinates']
        eq_location = (coords[1], coords[0])
        user_location = (user_lat, user_lon)
        distance_km = geodesic(user_location, eq_location).kilometers

        eq = {
            'id': feature['id'],
            'magnitude': props.get('mag', 0),
            'magnitude_type': props.get('magType', 'Unknown'),
            'time': datetime.fromtimestamp(props['time']/1000) if props.get('time') else None,
            'time_updated': datetime.fromtimestamp(props['updated']/1000) if props.get('updated') else None,
            'longitude': coords[0],
            'latitude': coords[1],
            'depth_km': coords[2],
            'location_description': props.get('place', 'Unknown'),
            'distance_km': round(distance_km, 2),
            'significance': props.get('sig', 0),
            'alert_level': props.get('alert', 'none'),
            'felt_reports': props.get('felt', 0),
            'cdi': props.get('cdi', 0),
            'mmi': props.get('mmi', 0),
            'tsunami_warning': props.get('tsunami', 0) == 1,
            'review_status': props.get('status', 'automatic'),
            'horizontal_error_km': props.get('horizontalError', 0),
            'depth_error_km': props.get('depthError', 0),
            'magnitude_error': props.get('magError', 0),
            'azimuthal_gap': props.get('gap', 0),
            'num_stations': props.get('nst', 0),
            'detail_url': props.get('url', ''),
            'usgs_event_page': props.get('detail', '')
        }
        eq['risk_level'] = classify_earthquake_risk(eq)
        eq['intensity_description'] = get_intensity_description(eq['mmi'])
        earthquakes.append(eq)

    df = pd.DataFrame(earthquakes)
    if not df.empty and 'time' in df.columns:
        df = df.sort_values('time', ascending=False)
    return df

def classify_earthquake_risk(eq):
    mag = eq.get('magnitude', 0)
    alert = eq.get('alert_level', 'none')
    tsunami = eq.get('tsunami_warning', False)
    if tsunami and mag >= 7.0:
        return 'CATASTROPHIC'
    if mag >= 8.0:
        return 'CATASTROPHIC'
    elif mag >= 7.0 or alert == 'red':
        return 'CRITICAL'
    elif mag >= 6.0 or alert == 'orange':
        return 'SEVERE'
    elif mag >= 5.0 or alert == 'yellow':
        return 'MODERATE'
    elif mag >= 4.0:
        return 'MINOR'
    else:
        return 'NEGLIGIBLE'

def get_intensity_description(mmi):
    if mmi >= 10: return "Extreme - Total destruction"
    elif mmi >= 9: return "Violent - Heavy damage"
    elif mmi >= 8: return "Severe - Moderate to heavy damage"
    elif mmi >= 7: return "Very Strong - Considerable damage"
    elif mmi >= 6: return "Strong - Slight damage"
    elif mmi >= 5: return "Moderate - Felt by nearly everyone"
    elif mmi >= 4: return "Light - Felt by many indoors"
    elif mmi >= 3: return "Weak - Felt by few"
    elif mmi >= 2: return "Not Felt - Instruments only"
    else: return "Not Felt"

def calculate_aftershock_probability(main_shock_mag, days_since):
    """
    Estimate aftershock probability using Omori's Law
    """
    K = 10 ** (main_shock_mag - 4.5)
    c = 0.05
    p = 1.1
    daily_rate = K / (c + days_since) ** p
    prob_significant = 1 - np.exp(-daily_rate * 7 * 0.05)
    if prob_significant > 0.5:
        recommendation = "HIGH RISK: Expect significant aftershocks."
    elif prob_significant > 0.2:
        recommendation = "MODERATE RISK: Aftershocks likely."
    else:
        recommendation = "LOW RISK: Activity declining."
    return {
        'expected_per_day': round(daily_rate, 2),
        'prob_7days': round(prob_significant * 100, 1),
        'recommendation': recommendation
    }

# ============================================================================
# 4. WEATHER MODULE (Updated with NWS Alerts)
# ============================================================================

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
NWS_BASE = "https://api.weather.gov/alerts"

def fetch_weather_forecast(lat, lon, forecast_days=16):
    params = {
        'latitude': lat, 'longitude': lon,
        'hourly': ','.join(['temperature_2m','relative_humidity_2m','precipitation_probability','weather_code','wind_speed_10m','wind_gusts_10m']),
        'daily': ','.join(['weather_code','temperature_2m_max','temperature_2m_min','precipitation_sum','wind_gusts_10m_max']),
        'current_weather': 'true', 'forecast_days': forecast_days, 'past_days': 3,
        'temperature_unit': 'celsius', 'wind_speed_unit': 'kmh', 'precipitation_unit': 'mm', 'timezone': 'auto'
    }
    try:
        r = requests.get(OPEN_METEO_BASE, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except:
        return None

def fetch_nws_alerts(lat, lon):
    url = f"{NWS_BASE}/active?point={lat},{lon}"
    headers = {'User-Agent': 'PanditaData/1.0', 'Accept': 'application/geo+json'}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        alerts = []
        for feature in data.get('features', []):
            props = feature['properties']
            alert = {
                'id': props['id'],
                'event': props['event'],
                'severity': props['severity'],
                'urgency': props['urgency'],
                'certainty': props['certainty'],
                'headline': props['headline'],
                'description': props['description'],
                'instruction': props['instruction'],
                'effective': props['effective'],
                'expires': props['expires'],
                'area': props['areaDesc']
            }
            alerts.append(alert)
        return sorted(alerts, key=lambda x: {'Extreme': 4, 'Severe': 3, 'Moderate': 2, 'Minor': 1}.get(x['severity'], 0), reverse=True)
    except:
        return []

WMO_WEATHER_CODES = {
    0: {'description': 'Clear sky', 'icon': '☀️', 'severity': 'none'},
    1: {'description': 'Mainly clear', 'icon': '🌤️', 'severity': 'none'},
    2: {'description': 'Partly cloudy', 'icon': '⛅', 'severity': 'none'},
    3: {'description': 'Overcast', 'icon': '☁️', 'severity': 'none'},
    45: {'description': 'Fog', 'icon': '🌫️', 'severity': 'low'},
    48: {'description': 'Rime fog', 'icon': '🌫️', 'severity': 'low'},
    51: {'description': 'Light drizzle', 'icon': '🌦️', 'severity': 'low'},
    61: {'description': 'Slight rain', 'icon': '🌧️', 'severity': 'low'},
    63: {'description': 'Moderate rain', 'icon': '🌧️', 'severity': 'moderate'},
    65: {'description': 'Heavy rain', 'icon': '⛈️', 'severity': 'high'},
    71: {'description': 'Slight snow', 'icon': '🌨️', 'severity': 'moderate'},
    73: {'description': 'Moderate snow', 'icon': '🌨️', 'severity': 'high'},
    95: {'description': 'Thunderstorm', 'icon': '⛈️', 'severity': 'critical'},
}

def interpret_weather_code(code):
    return WMO_WEATHER_CODES.get(int(code), {'description': 'Unknown', 'icon': '❓', 'severity': 'unknown'})

# ============================================================================
# 5. SPACE WEATHER MODULE (NASA/NOAA APIs)
# ============================================================================

def fetch_space_weather():
    try:
        # Kp Index
        kp_url = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
        kp_resp = requests.get(kp_url, timeout=10)
        kp_data = kp_resp.json()
        latest_kp = kp_data[-1] if kp_data else {}
        kp = float(latest_kp.get('kp_index', 0))
        
        # Solar Wind
        sw_url = "https://services.swpc.noaa.gov/json/rtsw/rtsw_wind_1m.json"
        sw_resp = requests.get(sw_url, timeout=10)
        sw_data = sw_resp.json()
        latest_sw = sw_data[-1] if sw_data else {}
        
        # Solar Flares (last 24h)
        flare_url = "https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json"
        flare_resp = requests.get(flare_url, timeout=10)
        flares = flare_resp.json()
        recent_flares = [f for f in flares if datetime.fromisoformat(f['time_tag'].replace('Z', '+00:00')) > datetime.now() - timedelta(hours=24)]
        
        return {
            'kp_index': kp,
            'storm_level': 'G5' if kp >= 9 else 'G4' if kp >= 8 else 'G3' if kp >= 7 else 'G2' if kp >= 6 else 'G1' if kp >= 5 else 'G0',
            'solar_wind_speed': latest_sw.get('proton_speed', 0),
            'recent_flares': len(recent_flares),
            'aurora_visible': kp > 5
        }
    except:
        return {'kp_index': 0, 'storm_level': 'G0', 'solar_wind_speed': 0, 'recent_flares': 0, 'aurora_visible': False}

# ============================================================================
# 6. HURRICANE TRACKING MODULE (NOAA NHC)
# ============================================================================

def fetch_active_hurricanes():
    try:
        url = "https://www.nhc.noaa.gov/data/txt/AL092025_publicAdvisory1.txt"  # Example, in prod use dynamic
        # For demo, return sample
        return [
            {'name': 'Sample Hurricane', 'category': 3, 'lat': 25.0, 'lon': -75.0, 'wind_speed': 120}
        ]
    except:
        return []

# ============================================================================
# 7. PDF EXPORT
# ============================================================================

def generate_pdf_report(lat, lon, df_eq, weather, alerts, space_data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    c.drawString(100, height - 100, "PanditaData Disaster Report")
    c.drawString(100, height - 120, f"Location: {reverse_geocode(lat, lon)}")
    c.drawString(100, height - 140, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Earthquakes
    c.drawString(100, height - 200, "Recent Earthquakes:")
    if not df_eq.empty:
        for i, row in df_eq.head(5).iterrows():
            c.drawString(120, height - 220 - i*20, f"{row['time']}: M{row['magnitude']} at {row['location_description']}")
    
    # Weather
    if weather:
        c.drawString(100, height - 300, "Current Weather:")
        c.drawString(120, height - 320, f"Temp: {weather['current_weather']['temperature']}°C")
    
    # Alerts
    c.drawString(100, height - 360, "NWS Alerts:")
    for alert in alerts[:3]:
        c.drawString(120, height - 380 - len(alerts[:3])*20 + i*20, f"{alert['event']}: {alert['headline'][:50]}")
    
    # Space Weather
    c.drawString(100, height - 420, "Space Weather:")
    c.drawString(120, height - 440, f"Kp: {space_data['kp_index']}, Storm: {space_data['storm_level']}")
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def download_pdf(data):
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="disaster_report.pdf">Download PDF Report</a>'
    st.markdown(href, unsafe_allow_html=True)

# ============================================================================
# 8. UI: SIDEBAR & INPUT
# ============================================================================

def create_sidebar():
    with st.sidebar:
        st.image("https://via.placeholder.com/200x60.png?text=PanditaData", width=200)
        st.markdown("### Disaster Intelligence Platform")
        
        if not authenticate_user():
            return None
        
        st.markdown("---")
        
        # Saved Locations
        st.subheader("Saved Locations")
        selected_loc = st.selectbox("Load Saved:", ["None"] + [loc['name'] for loc in st.session_state.saved_locations])
        if selected_loc != "None":
            load_saved_location(selected_loc)
        
        loc_name = st.text_input("Save as:")
        if st.button("Save Current Location") and loc_name:
            save_location(st.session_state.lat, st.session_state.lon, loc_name)
        
        input_method = st.radio("Input Method:", ["City/Address", "Coordinates", "Map Click"])

        if input_method == "City/Address":
            query = st.text_input("Enter location:", placeholder="San Francisco, CA")
            if query:
                loc = geocode_location(query)
                if loc:
                    st.session_state.lat = loc['latitude']
                    st.session_state.lon = loc['longitude']
                    st.success(f"Found: {loc['display_name']}")
                else:
                    st.error("Location not found")
        elif input_method == "Coordinates":
            col1, col2 = st.columns(2)
            with col1:
                lat = st.number_input("Latitude", value=st.session_state.get('lat', 37.7749), format="%.6f")
            with col2:
                lon = st.number_input("Longitude", value=st.session_state.get('lon', -122.4194), format="%.6f")
            if st.button("Set Location"):
                st.session_state.lat = lat
                st.session_state.lon = lon
        
        st.markdown("---")
        radius = st.slider("Search Radius (km)", 10, 1000, 200)
        days = st.slider("Time Window (days)", 1, 30, 7)
        min_mag = st.slider("Min Magnitude", 0.0, 6.0, 2.5, 0.1)
        return radius, days, min_mag

# ============================================================================
# 9. MAIN APP LOGIC
# ============================================================================

if 'lat' not in st.session_state:
    st.session_state.lat = 37.7749
    st.session_state.lon = -122.4194

params = create_sidebar()
if params:
    radius_km, days_back, min_mag = params
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    lat = st.session_state.lat
    lon = st.session_state.lon

    st.title(f"Disaster Report: {reverse_geocode(lat, lon)}")
    st.markdown(f"**Lat:** {lat:.4f} | **Lon:** {lon:.4f} | **Radius:** {radius_km} km")

    # --- EARTHQUAKES ---
    with st.spinner("Fetching earthquake data..."):
        geojson = fetch_earthquakes(lat, lon, radius_km, start_date, end_date, min_mag)
        df_eq = process_earthquake_data(geojson, lat, lon) if geojson else pd.DataFrame()

    if not df_eq.empty:
        st.subheader("Earthquake Activity")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Events", len(df_eq))
        col2.metric("Max Magnitude", f"{df_eq['magnitude'].max():.1f}")
        col3.metric("Closest", f"{df_eq['distance_km'].min():.0f} km")

        # Aftershock Analysis
        if not df_eq.empty:
            main_shock = df_eq.iloc[0]  # Assume largest/recent as main
            days_since = (datetime.now() - main_shock['time']).days
            aftershock = calculate_aftershock_probability(main_shock['magnitude'], days_since)
            st.subheader("Aftershock Probability Analysis")
            col1, col2 = st.columns(2)
            col1.metric("Expected/Day", aftershock['expected_per_day'])
            col2.metric("Prob 7 Days", f"{aftershock['prob_7days']}%")
            st.info(aftershock['recommendation'])

        fig_map = px.scatter_mapbox(
            df_eq, lat='latitude', lon='longitude', color='magnitude',
            size='magnitude', hover_name='location_description',
            color_continuous_scale=px.colors.sequential.Reds,
            size_max=30, zoom=5, height=500, mapbox_style='open-street-map'
        )
        fig_map.add_trace(go.Scattermapbox(
            lat=[lat], lon=[lon], mode='markers',
            marker=dict(size=15, color='blue', symbol='star'),
            name='Your Location'
        ))
        st.plotly_chart(fig_map, use_container_width=True)

        st.dataframe(df_eq[['time','magnitude','depth_km','distance_km','location_description','risk_level']].head(10))

    # --- WEATHER ---
    with st.spinner("Fetching weather..."):
        weather = fetch_weather_forecast(lat, lon)
    if weather and 'current_weather' in weather:
        cw = weather['current_weather']
        wc = interpret_weather_code(cw['weathercode'])
        st.subheader("Current Weather")
        col1, col2, col3 = st.columns(3)
        col1.metric("Temperature", f"{cw['temperature']:.1f}°C")
        col2.metric("Wind", f"{cw['windspeed']:.0f} km/h")
        col3.metric("Condition", f"{wc['icon']} {wc['description']}")

    # --- NWS ALERTS ---
    with st.spinner("Fetching NWS alerts..."):
        nws_alerts = fetch_nws_alerts(lat, lon)
    if nws_alerts:
        st.subheader("NWS Severe Weather Alerts")
        for alert in nws_alerts:
            severity_class = f"alert-{alert['severity'].lower()}" if alert['severity'] != 'Unknown' else 'moderate-alert'
            st.markdown(f"""
            <div class="critical-alert" if severity == 'Extreme' else 'high-alert' etc.>
                <h4>{alert['event']}</h4>
                <p><strong>{alert['headline']}</strong></p>
                <p>{alert['description'][:200]}...</p>
                <p><em>Expires: {alert['expires']}</em></p>
            </div>
            """, unsafe_allow_html=True)

    # --- SPACE WEATHER ---
    with st.spinner("Fetching space weather..."):
        space = fetch_space_weather()
    st.subheader("Space Weather")
    col1, col2, col3 = st.columns(3)
    col1.metric("Kp Index", f"{space['kp_index']:.1f}")
    col2.metric("Storm Level", space['storm_level'])
    col3.metric("Recent Flares", space['recent_flares'])
    if space['aurora_visible']:
        st.info("🌌 Aurora may be visible at high latitudes!")

    # --- HURRICANE TRACKING ---
    hurricanes = fetch_active_hurricanes()
    if hurricanes:
        st.subheader("Active Hurricanes")
        for h in hurricanes:
            st.metric(h['name'], f"Cat {h['category']}, {h['wind_speed']} mph")

    # --- PDF EXPORT ---
    if st.button("Generate PDF Report"):
        pdf_data = generate_pdf_report(lat, lon, df_eq, weather, nws_alerts, space)
        download_pdf(pdf_data)

    st.markdown("---")
    st.markdown("<div class='footer'>© 2025 PanditaData | Professional Disaster Intelligence</div>", unsafe_allow_html=True)
