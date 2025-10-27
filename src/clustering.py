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

def classify_suitability(score, high_threshold, medium_threshold):
    """
    Classify a user match score into a suitability tier based on thresholds.
    
    Parameters:
    -----------
    score : float
        User match score to classify.
    high_threshold : float
        Threshold for the 'Most Suitable' tier.
    medium_threshold : float
        Threshold for the 'Okay' tier.
    
    Returns:
    --------
    int
        Suitability tier (0 = Most Suitable, 1 = Okay, 2 = Less Suitable).
    """
    if score >= high_threshold:
        return 0  # Most Suitable
    elif score >= medium_threshold:
        return 1  # Okay
    else:
        return 2  # Less Suitable
    


def cluster_based_on_score(df_hexagons, score_column='user_match_score', 
                         threshold_percentiles=(0.67, 0.33), 
                         suitability_labels=None, 
                         clustering_method='threshold'):
    """
    Cluster hexagons into suitability tiers based on user match scores.
    
    Parameters:
    -----------
    df_hexagons : pd.DataFrame
        DataFrame containing hexagon data with user match scores.
    score_column : str, optional
        Column name containing the scores to cluster. Default is 'user_match_score'.
    threshold_percentiles : tuple, optional
        Percentiles for high and medium thresholds (e.g., (0.67, 0.33) for top 33% and middle 33%).
        Used only for threshold-based clustering. Default is (0.67, 0.33).
    suitability_labels : dict, optional
        Dictionary mapping tier indices to labels. Default is:
        {0: 'Most Suitable', 1: 'Okay', 2: 'Less Suitable'}
    clustering_method : str, optional
        Clustering method to use ('threshold' or 'dbscan'). Default is 'threshold'.
        Note: 'dbscan' is a placeholder for future implementation.
    
    Returns:
    --------
    pd.DataFrame
        Updated DataFrame with 'suitability' (tier index) and 'suitability_label' columns.
    """
    if suitability_labels is None:
        suitability_labels = {
            0: 'Most Suitable',
            1: 'Okay',
            2: 'Less Suitable'
        }
    
    df_hexagons = df_hexagons.copy()  # Avoid modifying the input DataFrame
    
    if clustering_method == 'threshold':
        # Calculate thresholds based on percentiles
        high_threshold, medium_threshold = df_hexagons[score_column].quantile(threshold_percentiles)
        print(f"\nThresholds: High = {high_threshold:.3f}, Medium = {medium_threshold:.3f}")
        
        # Apply classification
        df_hexagons['suitability'] = df_hexagons[score_column].apply(
            lambda x: classify_suitability(x, high_threshold, medium_threshold)
        )
    elif clustering_method == 'dbscan':
        # Placeholder for future DBSCAN implementation
        raise NotImplementedError("DBSCAN clustering is not yet implemented.")
    else:
        raise ValueError(f"Unknown clustering method: {clustering_method}. Choose 'threshold' or 'dbscan'.")
    
    # Map numerical tiers to readable labels
    df_hexagons['suitability_label'] = df_hexagons['suitability'].map(suitability_labels)
    
    # Print suitability distribution
    print(f"\nSuitability Distribution:")
    print(df_hexagons['suitability_label'].value_counts())
    
    # Print tier characteristics
    print("\n" + "="*60)
    print("SUITABILITY TIER CHARACTERISTICS")
    print("="*60)
    
    accessibility_columns = [col for col in df_hexagons.columns 
                           if col.endswith('_accessibility')]
    
    for tier in sorted(suitability_labels.keys()):
        tier_data = df_hexagons[df_hexagons['suitability'] == tier]
        label = suitability_labels[tier]
        print(f"\n{label} ({len(tier_data)} hexagons):")
        print(f"  Match Score Range: {tier_data[score_column].min():.3f} - {tier_data[score_column].max():.3f}")
        for col in accessibility_columns:
            print(f"  Avg {col.replace('_accessibility', ' Access')}: {tier_data[col].mean():.3f}")
    
    return df_hexagons