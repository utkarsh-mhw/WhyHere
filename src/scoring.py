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


def distance_decay_score(hex_center, pois_subset, decay_rate=1.5, max_distance_km=5):

    hex_lat, hex_lon = hex_center
    score = 0
    
    for _, poi in pois_subset.iterrows():
        lat_diff = abs(hex_lat - poi['lat'])
        lon_diff = abs(hex_lon - poi['lon'])
        distance_km = np.sqrt(lat_diff**2 + lon_diff**2) * 111
        
        if distance_km <= max_distance_km:
            score += 1 / (1 + distance_km) ** decay_rate
    
    return score


def calculate_accessibility_scores(hexagons, df_pois, poi_types_config=None):
    
    if poi_types_config is None:
        poi_types_config = {
            'restaurant': {'types': ['restaurant', 'cafe'], 'decay_rate': 2.0, 'max_distance_km': 2},
            'park': {'types': ['park'], 'decay_rate': 1.5, 'max_distance_km': 3},
            'clinic': {'types': ['clinic'], 'decay_rate': 1.0, 'max_distance_km': 5}
        }
    
    hex_data = []
    print("Calculating accessibility scores for each hexagon...")
    
    for i, hex_id in enumerate(hexagons):
        if i % 50 == 0:
            print(f"  Processing hexagon {i}/{len(hexagons)}...")
        
        hex_center = h3.cell_to_latlng(hex_id)
        hex_scores = {'hex_id': hex_id, 'lat': hex_center[0], 'lon': hex_center[1]}
        
        for poi_type, config in poi_types_config.items():
            pois_subset = df_pois[df_pois['type'].isin(config['types'])]
            score = distance_decay_score(
                hex_center,
                pois_subset,
                decay_rate=config['decay_rate'],
                max_distance_km=config['max_distance_km']
            )
            hex_scores[f"{poi_type}_accessibility"] = score
        
        hex_data.append(hex_scores)
    
    df_hexagons = pd.DataFrame(hex_data)
    print(f"\n✓ Calculated accessibility scores for {len(df_hexagons)} hexagons")
    
    print("\nAccessibility Score Statistics:")
    score_columns = [f"{poi_type}_accessibility" for poi_type in poi_types_config]
    print(df_hexagons[score_columns].describe())
    
    return df_hexagons


def apply_user_weights(df_hexagons, user_weights):
    
    print("\nApplying User Weights")
    print(f"User preferences: {user_weights}")
    print(f"Sum of weights: {sum(user_weights.values()):.2f} (should be 1.0)")
    
    # Normalize accessibility scores to 0-1 range
    scaler = MinMaxScaler()
    df_hexagons = df_hexagons.copy()  # Avoid modifying the input DataFrame
    
    for poi_type in user_weights:
        score_column = f"{poi_type}_accessibility"
        norm_column = f"{poi_type}_norm"
        if score_column in df_hexagons.columns:
            df_hexagons[norm_column] = scaler.fit_transform(df_hexagons[[score_column]])
        else:
            raise ValueError(f"Accessibility score for {poi_type} not found in DataFrame")
    
    # Calculate weighted match score
    df_hexagons['user_match_score'] = 0.0
    for poi_type, weight in user_weights.items():
        norm_column = f"{poi_type}_norm"
        if norm_column in df_hexagons.columns:
            df_hexagons['user_match_score'] += df_hexagons[norm_column] * weight
    
    print(f"\nUser Match Score Statistics:")
    print(df_hexagons['user_match_score'].describe())
    
    return df_hexagons