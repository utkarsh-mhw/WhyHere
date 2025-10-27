import sys
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
import folium
import json
import time
import numpy as np
import h3
from folium.plugins import HeatMap
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import MinMaxScaler


def create_hex_grids(df_pois, size_of_grid = 8):


    h3_resolution = size_of_grid
    ATLANTA_CENTER = (33.749, -84.388)

    lat_min, lat_max = df_pois['lat'].min(), df_pois['lat'].max()
    lon_min, lon_max = df_pois['lon'].min(), df_pois['lon'].max()

    hexagons = set()
    for lat in np.linspace(lat_min, lat_max, 50):
        for lon in np.linspace(lon_min, lon_max, 50):
            hex_id = h3.latlng_to_cell(lat, lon, h3_resolution)
            hexagons.add(hex_id)

    hexagons = list(hexagons)
    print(f"Generated {len(hexagons)} hexagons at resolution {h3_resolution}")

    return hexagons