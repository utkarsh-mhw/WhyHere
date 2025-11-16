import os
import sys
from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import json
from src.fetch_csv_data import *
from src import *

# ====================================================================
# Configuration
# ====================================================================

# Add the src directory to the system path so we can import modules
# This is crucial for accessing fetch_data, scoring, etc.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'input_data')
RESULT_MAPS_DIR = os.path.join(BASE_DIR, 'static', 'result_maps')

# Ensure the result map directory exists
os.makedirs(RESULT_MAPS_DIR, exist_ok=True)

app = Flask(__name__)

# ====================================================================
# Import Analysis Modules (Placeholder Imports)
# ====================================================================
# IMPORTANT: You will need to uncomment and adjust these imports
# based on which functions you need to call directly.

# from fetch_data import query_restaurant_data, query_park_data, query_hospital_and_clinic_data
# from data_io import load_pois, save_map
# from data_prep import create_hex_grids_with_radius
# from scoring import calculate_accessibility_scores, apply_user_weights
# from dbscan_clustering import dbscan_spatial_clustering, get_cluster_colors
# from visualization import create_dbscan_map


# A list of POI types the user can weight
POI_TYPES = ['restaurant', 'park', 'clinic']


# ====================================================================
# Routes
# ====================================================================

@app.route('/')
def index():
    """Renders the main input form."""
    return render_template('index.html', poi_types=POI_TYPES)

@app.route('/data/pois', methods=['POST'])
def get_poi_data():
    """
    Fetches POI data from Databricks using the configured table name 
    and returns a status and record count.
    
    Example usage: GET /data/pois?table=my_catalog.my_schema.my_pois
    """
    # Allows the user to specify a different table name via query parameter
    # default_table = 'workspace.default.restaurants'
    # table_name = request.args.get('table', default_table)
    
    try:
        # Call the data loader function
        df_pois = load_pois()
        
        #call data_prep method here, providing df_pois as input

        #call scoring method here, providing scored data as input

        #call clustering method here, providing scored data as input

        #call visualization method here (if needed to return map data)

        #then replace the below data key's value (df_pois) with the data generated from visualization method or clustering method as needed

        if len(df_pois) == 0:
            return jsonify({
                'success': False, 
                'message': f'Failed to load POI data from CSV file.'
            }), 500
        
        return jsonify({
            'success': True,
            'message': f'Successfully loaded {len(df_pois)} Points of Interest.',
            'record_count': len(df_pois),
            'data':df_pois
        }), 200

    except ValueError as ve:
        # Catch specific data validation errors (e.g., missing columns)
        return jsonify({
            'success': False, 
            'message': f'Data Validation Error: {str(ve)}'
        }), 400
    except Exception as e:
        print(f"Error fetching data via API: {e}", file=sys.stderr)
        return jsonify({
            'success': False, 
            'message': f'An unexpected error occurred during Databricks fetch: {str(e)}'
        }), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Handles the user's input (weights) and runs the geospatial analysis pipeline.
    """
    try:
        # 1. Parse User Input (Weights)
        user_weights = {}
        total_weight = 0.0
        
        for poi in POI_TYPES:
            weight = float(request.form.get(f'weight_{poi}', 0)) / 100.0 # Convert percentage to float
            user_weights[poi] = weight
            total_weight += weight
            
        # Basic Validation
        if abs(total_weight - 1.0) > 0.01:
            return jsonify({'success': False, 'message': 'Total weights must sum to 100%.'}), 400

        print(f"User Weights Received: {user_weights}")

        # 2. RUN THE GEOSPATIAL PIPELINE (Main Integration Point)
        
        # --- PHASE 1: Data Loading ---
        # NOTE: For a real app, you'd likely pre-calculate and save the hexagon
        # data to avoid 30-second load times on every request.
        
        # Example of loading pre-processed data (RECOMMENDED for Flask performance)
        # df_hexagons = pd.read_csv(os.path.join(DATA_DIR, 'pre_calculated_hex_data.csv'))

        # --- PHASE 2: Re-scoring (If necessary, use user_weights) ---
        
        # map_filename = f"analysis_map_{hash(json.dumps(user_weights))}.html"
        map_filename = "latest_analysis_result.html" # Simple name for this demo

        
        # ----------------------------------------------------------------------
        # PLACEHOLDER FOR YOUR ANALYSIS LOGIC:
        # Replace this block with your actual code flow using the user_weights.
        # 
        # try:
        #     # 1. Load POIs/Hexagons
        #     df_pois = load_pois('atlanta_pois')
        #     
        #     # 2. Calculate Final Scores (using scoring.py)
        #     # This assumes you have the base accessibility scores already calculated
        #     # and saved in a DataFrame, or you calculate them here.
        #     # df_hexagons_scored = apply_user_weights(df_hexagons, user_weights) 
        #     
        #     # 3. Run Clustering (using dbscan_clustering.py)
        #     # df_clustered = dbscan_spatial_clustering(df_hexagons_scored, ...)
        #     
        #     # 4. Generate Map (using visualization.py and data_io.py)
        #     # folium_map = create_dbscan_map(df_clustered, user_weights, ...)
        #     # save_map(folium_map, os.path.join(RESULT_MAPS_DIR, map_filename))
        #     
        #     # SIMULATED SUCCESS: Create a dummy map file for demonstration
        #     with open(os.path.join(RESULT_MAPS_DIR, map_filename), 'w') as f:
        #         f.write(f"<html><body><h1>Suitability Map for {user_weights}</h1><p>This is a simulated Folium map result. Integrate your `visualization.py` here!</p></body></html>")
        # 
        # except Exception as e:
        #     print(f"Analysis failed: {e}", file=sys.stderr)
        #     return jsonify({'success': False, 'message': f'Analysis failed: {str(e)}'}), 500
        # ----------------------------------------------------------------------

        # SIMULATED SUCCESS: The map file is now available in static/result_maps/
        return jsonify({'success': True, 'map_url': f'/static/result_maps/{map_filename}'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'An unexpected error occurred: {str(e)}'}), 500


# ====================================================================
# Startup
# ====================================================================

if __name__ == '__main__':
    # When deploying, set debug=False
    app.run(debug=True)