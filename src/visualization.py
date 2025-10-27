import pandas as pd
import folium
from shapely.geometry import Polygon
import h3
import numpy as np
from sklearn.cluster import DBSCAN  # Retained for future DBSCAN support

def hex_to_polygon(hex_id):
    """
    Convert an H3 hexagon ID to a Shapely polygon.
    
    Parameters:
    -----------
    hex_id : str
        H3 hexagon ID.
    
    Returns:
    --------
    shapely.geometry.Polygon
        Polygon representing the hexagon's boundary.
    """
    try:
        boundary = h3.cell_to_boundary(hex_id)
        return Polygon([(lon, lat) for lat, lon in boundary])
    except Exception as e:
        raise ValueError(f"Failed to convert hex_id {hex_id} to polygon: {str(e)}")

def generate_color_scale(n_clusters, colormap=None):
    """
    Generate a color scale for clusters using hardcoded colors matching the original scheme.
    
    Parameters:
    -----------
    n_clusters : int
        Number of clusters (suitability tiers).
    colormap : str, optional
        Ignored in this implementation (kept for compatibility).
    
    Returns:
    --------
    dict
        Dictionary mapping cluster indices (0 to n_clusters-1) to hex colors.
    """
    # Hardcoded colors from original code
    default_colors = {
        0: '#2ecc71',  # Green - Most Suitable
        1: '#f39c12',  # Orange - Okay
        2: '#e74c3c'   # Red - Less Suitable
    }
    if n_clusters > len(default_colors):
        raise ValueError(f"Number of clusters ({n_clusters}) exceeds available colors ({len(default_colors)})")
    colors = {i: default_colors[i] for i in range(n_clusters)}
    print(f"Color mapping for {n_clusters} clusters: {colors}")
    return colors

def create_suitability_map(df_hexagons, user_weights, center=(33.749, -84.388), 
                         zoom_start=11, tiles='CartoDB positron', 
                         colormap=None, title='Area Suitability Map', 
                         suitability_column='suitability', 
                         label_column='suitability_label', 
                         score_column='user_match_score', 
                         accessibility_columns=None):
    """
    Create a Folium map visualizing hexagon suitability tiers.
    
    Parameters:
    -----------
    df_hexagons : pd.DataFrame
        DataFrame containing hexagon data with suitability tiers, labels, and scores.
    user_weights : dict
        Dictionary of user weights for POI types (e.g., {'restaurant': 0.5, 'park': 0.1, 'clinic': 0.4}).
    center : tuple, optional
        Map center coordinates (latitude, longitude). Default is Atlanta center (33.749, -84.388).
    zoom_start : int, optional
        Initial zoom level for the map. Default is 11.
    tiles : str, optional
        Folium map tile style. Default is 'CartoDB positron'.
    colormap : str, optional
        Ignored in this implementation (kept for compatibility).
    title : str, optional
        Title for the map. Default is 'Area Suitability Map'.
    suitability_column : str, optional
        Column name for suitability tier indices. Default is 'suitability'.
    label_column : str, optional
        Column name for suitability labels. Default is 'suitability_label'.
    score_column : str, optional
        Column name for user match scores. Default is 'user_match_score'.
    accessibility_columns : list, optional
        List of columns for accessibility scores to display in popups. 
        If None, defaults to columns ending with '_accessibility'.
    
    Returns:
    --------
    folium.Map
        Folium map object with hexagons, title, and legend.
    """
    # Validate input DataFrame
    required_columns = ['hex_id', suitability_column, label_column, score_column]
    missing_columns = [col for col in required_columns if col not in df_hexagons.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns in df_hexagons: {missing_columns}")
    
    # Print suitability distribution for debugging
    print(f"Suitability distribution:\n{df_hexagons[suitability_column].value_counts().sort_index()}")
    
    # Determine accessibility columns if not provided
    if accessibility_columns is None:
        accessibility_columns = [col for col in df_hexagons.columns if col.endswith('_accessibility')]
    if not accessibility_columns:
        print("Warning: No accessibility columns found. Popups will only show match score.")
    
    # Validate accessibility columns
    invalid_access_cols = [col for col in accessibility_columns if col not in df_hexagons.columns]
    if invalid_access_cols:
        raise ValueError(f"Invalid accessibility columns: {invalid_access_cols}")
    
    # Initialize map
    m = folium.Map(location=center, zoom_start=zoom_start, tiles=tiles)
    
    # Generate colors based on the number of unique suitability tiers
    n_clusters = df_hexagons[suitability_column].nunique()
    colors = generate_color_scale(n_clusters, colormap=colormap)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%); 
                width: 700px; height: auto; background-color: white; border:2px solid grey; 
                z-index:9999; font-size:16px; font-weight:bold; padding: 15px; text-align: center;">
        {title}<br>
        <span style="font-size: 13px; font-weight: normal; color: #666;">
        User Preferences: {', '.join([f'{k.capitalize()}: {v*100:.0f}%' for k, v in user_weights.items()])}
        </span>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add hexagons
    print("Adding hexagons to map...")
    for idx, row in df_hexagons.iterrows():
        if idx % 50 == 0:
            print(f"  Added {idx}/{len(df_hexagons)} hexagons...")
        
        try:
            polygon = hex_to_polygon(row['hex_id'])
            tier = row[suitability_column]
            
            # Ensure tier has a corresponding color
            if tier not in colors:
                print(f"Warning: Suitability tier {tier} not in color scale. Skipping hexagon {row['hex_id']}.")
                continue
            
            # Create popup content
            popup_content = f"""
                <b>{row[label_column]}</b><br>
                Match Score: {row[score_column]:.3f}<br><br>
                <b>Accessibility Scores:</b><br>
                {''.join([f"{col.replace('_accessibility', '').capitalize()}: {row[col]:.2f}<br>" 
                          for col in accessibility_columns])}
            """
            
            folium.Polygon(
                locations=[(lat, lon) for lon, lat in polygon.exterior.coords],
                color=colors[tier],
                fill=True,
                fill_color=colors[tier],
                fill_opacity=0.6,
                weight=1,
                popup=popup_content
            ).add_to(m)
        except Exception as e:
            print(f"Warning: Failed to add hexagon {row['hex_id']}: {str(e)}")
    
    # Add legend
    label_counts = df_hexagons[label_column].value_counts().to_dict()
    legend_html = f'''
    <div style="position: fixed; bottom: 50px; left: 50px; 
                background-color: white; padding: 15px; 
                border: 2px solid grey; z-index: 9999; font-size: 14px;">
        <p style="margin: 0 0 10px 0; font-weight: bold;">Area Suitability</p>
        {''.join([f'<p style="margin: 5px 0;"><span style="color:{colors[tier]}; font-size: 20px;">●</span> {label} ({label_counts.get(label, 0)} areas)</p>' 
                  for tier, label in sorted(df_hexagons[[suitability_column, label_column]].drop_duplicates().set_index(suitability_column)[label_column].to_dict().items())])}
        <p style="margin: 15px 0 5px 0; font-weight: bold; border-top: 1px solid #ccc; padding-top: 10px;">User Weights</p>
        {''.join([f'<p style="margin: 5px 0; font-size: 12px;">{k.capitalize()}: {v*100:.0f}%</p>' 
                  for k, v in user_weights.items()])}
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m