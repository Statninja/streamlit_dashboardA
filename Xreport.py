import requests
import geopandas as gpd
import pandas as pd
import streamlit as st

def fetch_usgs_earthquake_data(starttime, endtime, latitude=None, longitude=None, maxradiuskm=None):
    """
    Fetches earthquake data from the USGS API and returns a GeoPandas GeoDataFrame.
    """
    base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        'format': 'geojson',
        'starttime': starttime,
        'endtime': endtime,
        'latitude': latitude,
        'longitude': longitude,
        'maxradiuskm': maxradiuskm,
        'orderby': 'time'  # Orders by time, most recent first
    }
    # Remove parameters that are None
    params = {k: v for k, v in params.items() if v is not None}
    
    response = requests.get(base_url, params=params)
    data = response.json()
    
    # Convert the GeoJSON features to a GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features(data['features'])
    
    # Extract coordinates for distance calculation if a location was provided
    if latitude and longitude:
        from shapely.geometry import Point
        user_location = Point(longitude, latitude)
        gdf['distance_km'] = gdf.geometry.distance(user_location) * 111  # Approximate conversion to km
    
    return gdf
