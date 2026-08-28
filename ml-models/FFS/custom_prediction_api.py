#!/usr/bin/env python3
"""
Simple API for custom food freshness model.
Works with your dataset columns: food_type, temperature_c, humidity_percent, gas_ppm, day, spoiled, remaining_days
"""

import os
import sys
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from models.custom_food_model import CustomFoodModel

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load the trained model
model = CustomFoodModel()
model_file = "custom_food_model.pkl"

if os.path.exists(model_file):
    model.load_model(model_file)
    print("✅ Model loaded successfully")
else:
    print(f"❌ Model file '{model_file}' not found. Please train the model first.")
    print("Run: python train_custom_model.py")
    model = None

@app.route('/')
def home():
    """API home page with usage instructions"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Custom Food Freshness API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { color: #007bff; font-weight: bold; }
            .path { font-family: monospace; background: #e9ecef; padding: 2px 5px; }
            pre { background: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>🍎 Custom Food Freshness API</h1>
        <p>API for food freshness prediction with your custom dataset format</p>
        
        <h2>Dataset Columns:</h2>
        <ul>
            <li>food_type</li>
            <li>temperature_c</li>
            <li>humidity_percent</li>
            <li>gas_ppm</li>
            <li>day</li>
            <li>spoiled (target)</li>
            <li>remaining_days (target)</li>
        </ul>
        
        <h2>Available Endpoints:</h2>
        
        <div class="endpoint">
            <span class="method">POST</span> <span class="path">/predict</span>
            <p>Make a single prediction</p>
            <pre>{
  "food_type": "leafy_greens",
  "temperature_c": 4.5,
  "humidity_percent": 85.0,
  "gas_ppm": 0.3,
  "day": 2
}</pre>
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span> <span class="path">/predict/batch</span>
            <p>Make batch predictions</p>
            <pre>{
  "items": [
    {"food_type": "leafy_greens", "temperature_c": 4.5, "humidity_percent": 85.0, "gas_ppm": 0.3, "day": 2},
    {"food_type": "burgers", "temperature_c": 5.0, "humidity_percent": 80.0, "gas_ppm": 0.8, "day": 3}
  ]
}</pre>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <span class="path">/model/info</span>
            <p>Get model information</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <span class="path">/health</span>
            <p>Health check</p>
        </div>
        
        <h2>Response Format:</h2>
        <pre>{
  "food_type": "leafy_greens",
  "temperature_c": 4.5,
  "humidity_percent": 85.0,
  "gas_ppm": 0.3,
  "day": 2,
  "spoiled_prediction": false,
  "spoiled_probability": 0.15,
  "freshness_percentage": 85.0,
  "status": "good",
  "remaining_days": 3.2,
  "confidence": 0.85
}</pre>
    </body>
    </html>
    """
    return html

@app.route('/predict', methods=['POST'])
def predict():
    """Make a single prediction"""
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['food_type', 'temperature_c', 'humidity_percent', 'gas_ppm', 'day']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
        
        # Make prediction
        prediction = model.predict(
            food_type=data['food_type'],
            temperature_c=float(data['temperature_c']),
            humidity_percent=float(data['humidity_percent']),
            gas_ppm=float(data['gas_ppm']),
            day=float(data['day'])
        )
        
        return jsonify(prediction)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict/batch', methods=['POST'])
def predict_batch():
    """Make batch predictions"""
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        data = request.get_json()
        
        if 'items' not in data:
            return jsonify({'error': 'Missing items field'}), 400
        
        items = data['items']
        if not isinstance(items, list):
            return jsonify({'error': 'Items must be a list'}), 400
        
        # Make batch predictions
        predictions = model.predict_batch(items)
        
        return jsonify({
            'predictions': predictions,
            'total_items': len(items),
            'successful_predictions': len([p for p in predictions if 'error' not in p])
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/model/info', methods=['GET'])
def model_info():
    """Get model information"""
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        info = model.get_model_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy' if model is not None else 'unhealthy',
        'model_loaded': model is not None,
        'model_file': model_file
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🍎 Starting Custom Food Freshness API...")
    print("📁 Model file:", model_file)
    print("🌐 API will be available at: http://localhost:5000")
    print("📖 Documentation: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
