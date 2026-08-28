#!/usr/bin/env python3
"""
Simple HTTP API for your food model (no Flask needed!)
"""

import sys
import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from models.custom_food_model import CustomFoodModel

# Load your model
model = CustomFoodModel()
try:
    model.load_model('custom_food_model.pkl')
    print("✅ Model loaded successfully")
except:
    print("❌ Model not found. Please run: python train_custom_model.py")
    sys.exit(1)

class FoodAPIHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>🍎 Food Freshness API</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }
                    
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        color: #333;
                    }
                    
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    
                    .header {
                        text-align: center;
                        margin-bottom: 40px;
                        color: white;
                    }
                    
                    .header h1 {
                        font-size: 3rem;
                        margin-bottom: 10px;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    }
                    
                    .header p {
                        font-size: 1.2rem;
                        opacity: 0.9;
                    }
                    
                    .card {
                        background: white;
                        border-radius: 15px;
                        padding: 30px;
                        margin-bottom: 30px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                        transition: transform 0.3s ease;
                    }
                    
                    .card:hover {
                        transform: translateY(-5px);
                    }
                    
                    .card h2 {
                        color: #667eea;
                        margin-bottom: 20px;
                        font-size: 1.8rem;
                        display: flex;
                        align-items: center;
                        gap: 10px;
                    }
                    
                    .endpoint {
                        background: #f8f9fa;
                        border-left: 4px solid #667eea;
                        padding: 20px;
                        margin: 20px 0;
                        border-radius: 8px;
                    }
                    
                    .method {
                        display: inline-block;
                        background: #667eea;
                        color: white;
                        padding: 5px 12px;
                        border-radius: 20px;
                        font-weight: bold;
                        font-size: 0.9rem;
                        margin-bottom: 10px;
                    }
                    
                    .path {
                        font-family: 'Courier New', monospace;
                        background: #e9ecef;
                        padding: 8px 12px;
                        border-radius: 5px;
                        color: #495057;
                        font-weight: bold;
                    }
                    
                    pre {
                        background: #2d3748;
                        color: #e2e8f0;
                        padding: 20px;
                        border-radius: 8px;
                        overflow-x: auto;
                        font-family: 'Courier New', monospace;
                        font-size: 0.9rem;
                        line-height: 1.5;
                    }
                    
                    .status-indicator {
                        display: inline-block;
                        width: 12px;
                        height: 12px;
                        background: #28a745;
                        border-radius: 50%;
                        margin-right: 8px;
                        animation: pulse 2s infinite;
                    }
                    
                    @keyframes pulse {
                        0% { opacity: 1; }
                        50% { opacity: 0.5; }
                        100% { opacity: 1; }
                    }
                    
                    .food-types {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 10px;
                        margin-top: 15px;
                    }
                    
                    .food-type {
                        background: #f1f3f4;
                        padding: 8px 12px;
                        border-radius: 20px;
                        text-align: center;
                        font-size: 0.9rem;
                        transition: all 0.3s ease;
                    }
                    
                    .food-type:hover {
                        background: #667eea;
                        color: white;
                        transform: scale(1.05);
                    }
                    
                    .test-button {
                        background: #28a745;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 25px;
                        font-size: 1rem;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        margin-top: 15px;
                    }
                    
                    .test-button:hover {
                        background: #218838;
                        transform: translateY(-2px);
                    }
                    
                    .response-box {
                        background: #d4edda;
                        border: 1px solid #c3e6cb;
                        border-radius: 8px;
                        padding: 15px;
                        margin-top: 15px;
                        display: none;
                    }
                    
                    .footer {
                        text-align: center;
                        color: white;
                        margin-top: 40px;
                        opacity: 0.8;
                    }
                    
                    @media (max-width: 768px) {
                        .header h1 {
                            font-size: 2rem;
                        }
                        
                        .card {
                            padding: 20px;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🍎 Food Freshness API</h1>
                        <p>Intelligent Food Safety Prediction System</p>
                        <div style="margin-top: 20px;">
                            <span class="status-indicator"></span>
                            <span>API Status: Online & Ready</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>🚀 Quick Test</h2>
                        <p>Try our prediction API with sample data!</p>
                        <button class="test-button" onclick="testPrediction()">Test Sample Prediction</button>
                        <div id="response-box" class="response-box"></div>
                    </div>
                    
                    <div class="card">
                        <h2>🧪 Custom Prediction</h2>
                        <p>Enter your own food data to test the prediction:</p>
                        <form id="prediction-form" style="margin-top: 20px;">
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Food Type:</label>
                                    <select id="food-type" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 5px;">
                                        <option value="leafy_greens">🥬 Leafy Greens</option>
                                        <option value="burgers">🍔 Burgers</option>
                                        <option value="canned_goods">🥫 Canned Goods</option>
                                        <option value="dry_goods">🌾 Dry Goods</option>
                                        <option value="fried_items">🍟 Fried Items</option>
                                        <option value="frozen_foods">🧊 Frozen Foods</option>
                                        <option value="fruits">🍎 Fruits</option>
                                        <option value="herbs">🌿 Herbs</option>
                                        <option value="homemade">🏠 Homemade</option>
                                        <option value="leftovers">🍕 Leftovers</option>
                                        <option value="pizza">🍕 Pizza</option>
                                        <option value="prepared_meals">🍽️ Prepared Meals</option>
                                        <option value="restaurant_food">🏪 Restaurant Food</option>
                                        <option value="sandwiches">🥪 Sandwiches</option>
                                        <option value="snacks">🍿 Snacks</option>
                                        <option value="vegetables">🥕 Vegetables</option>
                                    </select>
                                </div>
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Temperature (°C):</label>
                                    <input type="number" id="temperature" step="0.1" value="4.5" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 5px;">
                                </div>
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Humidity (%):</label>
                                    <input type="number" id="humidity" step="0.1" value="85.0" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 5px;">
                                </div>
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Gas Concentration (ppm):</label>
                                    <input type="number" id="gas" step="0.01" value="0.3" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 5px;">
                                </div>
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Days Since Storage:</label>
                                    <input type="number" id="days" step="0.1" value="2" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 5px;">
                                </div>
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Quick Presets:</label>
                                    <select id="presets" onchange="loadPreset()" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 5px;">
                                        <option value="">Custom Input</option>
                                        <option value="fresh-greens">🥬 Fresh Leafy Greens</option>
                                        <option value="spoiling-burger">🍔 Spoiling Burger</option>
                                        <option value="good-canned">🥫 Good Canned Goods</option>
                                        <option value="old-herbs">🌿 Old Herbs</option>
                                        <option value="fresh-fruits">🍎 Fresh Fruits</option>
                                        <option value="bad-leftovers">🍕 Bad Leftovers</option>
                                    </select>
                                </div>
                            </div>
                            <button type="submit" class="test-button" style="margin-top: 20px; background: #667eea;">🔮 Predict Freshness</button>
                        </form>
                        <div id="custom-response-box" class="response-box"></div>
                    </div>
                    
                    <div class="card">
                        <h2>📡 Available Endpoints</h2>
                        
                        <div class="endpoint">
                            <div class="method">POST</div>
                            <div class="path">/predict</div>
                            <p><strong>Make a single prediction</strong></p>
                            <pre>{
  "food_type": "leafy_greens",
  "temperature_c": 4.5,
  "humidity_percent": 85.0,
  "gas_ppm": 0.3,
  "day": 2
}</pre>
                        </div>
                        
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="path">/model/info</div>
                            <p><strong>Get model information</strong></p>
                        </div>
                        
                        <div class="endpoint">
                            <div class="method">GET</div>
                            <div class="path">/health</div>
                            <p><strong>Health check</strong></p>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>📊 Response Format</h2>
                        <pre>{
  "status": "fresh",
  "freshness_percentage": 96.0,
  "remaining_days": 4.0,
  "confidence": 0.96,
  "spoiled_prediction": false,
  "spoiled_probability": 0.04
}</pre>
                    </div>
                    
                    <div class="card">
                        <h2>🍎 Supported Food Types</h2>
                        <p>Our AI can predict freshness for 16 different food categories:</p>
                        <div class="food-types">
                            <div class="food-type">🍔 burgers</div>
                            <div class="food-type">🥫 canned_goods</div>
                            <div class="food-type">🌾 dry_goods</div>
                            <div class="food-type">🍟 fried_items</div>
                            <div class="food-type">🧊 frozen_foods</div>
                            <div class="food-type">🍎 fruits</div>
                            <div class="food-type">🌿 herbs</div>
                            <div class="food-type">🏠 homemade</div>
                            <div class="food-type">🥬 leafy_greens</div>
                            <div class="food-type">🍕 leftovers</div>
                            <div class="food-type">🍕 pizza</div>
                            <div class="food-type">🍽️ prepared_meals</div>
                            <div class="food-type">🏪 restaurant_food</div>
                            <div class="food-type">🥪 sandwiches</div>
                            <div class="food-type">🍿 snacks</div>
                            <div class="food-type">🥕 vegetables</div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h2>📈 Model Performance</h2>
                        <p>Our AI model achieves impressive accuracy:</p>
                        <ul style="margin-left: 20px; margin-top: 15px;">
                            <li><strong>Accuracy:</strong> 93.3% for spoilage detection</li>
                            <li><strong>RMSE:</strong> 1.82 days for shelf life prediction</li>
                            <li><strong>R² Score:</strong> 0.9991 for regression</li>
                            <li><strong>Training Data:</strong> 5,000 diverse food samples</li>
                        </ul>
                    </div>
                    
                    <div class="footer">
                        <p>🚀 Powered by Machine Learning | Built with ❤️ for Food Safety</p>
                    </div>
                </div>
                
                <script>
                    // Presets data
                    const presets = {
                        'fresh-greens': { food_type: 'leafy_greens', temperature: 4.0, humidity: 95.0, gas: 0.1, days: 1 },
                        'spoiling-burger': { food_type: 'burgers', temperature: 8.0, humidity: 70.0, gas: 0.8, days: 3 },
                        'good-canned': { food_type: 'canned_goods', temperature: 20.0, humidity: 60.0, gas: 0.05, days: 100 },
                        'old-herbs': { food_type: 'herbs', temperature: 6.0, humidity: 100.0, gas: 0.4, days: 2.8 },
                        'fresh-fruits': { food_type: 'fruits', temperature: 5.0, humidity: 90.0, gas: 0.2, days: 2 },
                        'bad-leftovers': { food_type: 'leftovers', temperature: 7.0, humidity: 80.0, gas: 0.9, days: 4 }
                    };
                    
                    function loadPreset() {
                        const presetSelect = document.getElementById('presets');
                        const preset = presets[presetSelect.value];
                        
                        if (preset) {
                            document.getElementById('food-type').value = preset.food_type;
                            document.getElementById('temperature').value = preset.temperature;
                            document.getElementById('humidity').value = preset.humidity;
                            document.getElementById('gas').value = preset.gas;
                            document.getElementById('days').value = preset.days;
                        }
                    }
                    
                    async function testPrediction() {
                        const responseBox = document.getElementById('response-box');
                        const button = document.querySelector('.test-button');
                        
                        button.textContent = 'Testing...';
                        button.disabled = true;
                        
                        try {
                            const response = await fetch('/predict', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    food_type: 'leafy_greens',
                                    temperature_c: 4.5,
                                    humidity_percent: 85.0,
                                    gas_ppm: 0.3,
                                    day: 2
                                })
                            });
                            
                            const result = await response.json();
                            
                            responseBox.style.display = 'block';
                            responseBox.innerHTML = `
                                <h3>✅ Sample Prediction Result</h3>
                                <p><strong>Food:</strong> ${result.food_type}</p>
                                <p><strong>Status:</strong> <span style="color: ${result.freshness_percentage > 70 ? '#28a745' : result.freshness_percentage > 30 ? '#ffc107' : '#dc3545'}">${result.status.toUpperCase()}</span></p>
                                <p><strong>Freshness:</strong> ${result.freshness_percentage.toFixed(1)}%</p>
                                <p><strong>Remaining Days:</strong> ${result.remaining_days.toFixed(1)}</p>
                                <p><strong>Confidence:</strong> ${(result.confidence * 100).toFixed(1)}%</p>
                            `;
                            
                        } catch (error) {
                            responseBox.style.display = 'block';
                            responseBox.style.background = '#f8d7da';
                            responseBox.style.borderColor = '#f5c6cb';
                            responseBox.innerHTML = `<h3>❌ Error</h3><p>${error.message}</p>`;
                        }
                        
                        button.textContent = 'Test Sample Prediction';
                        button.disabled = false;
                    }
                    
                    // Handle custom form submission
                    document.getElementById('prediction-form').addEventListener('submit', async function(e) {
                        e.preventDefault();
                        
                        const responseBox = document.getElementById('custom-response-box');
                        const button = e.target.querySelector('button[type="submit"]');
                        
                        button.textContent = 'Predicting...';
                        button.disabled = true;
                        
                        try {
                            const formData = {
                                food_type: document.getElementById('food-type').value,
                                temperature_c: parseFloat(document.getElementById('temperature').value),
                                humidity_percent: parseFloat(document.getElementById('humidity').value),
                                gas_ppm: parseFloat(document.getElementById('gas').value),
                                day: parseFloat(document.getElementById('days').value)
                            };
                            
                            const response = await fetch('/predict', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify(formData)
                            });
                            
                            const result = await response.json();
                            
                            responseBox.style.display = 'block';
                            responseBox.innerHTML = `
                                <h3>🔮 Custom Prediction Result</h3>
                                <p><strong>Input Data:</strong></p>
                                <ul style="margin-left: 20px; margin-bottom: 15px;">
                                    <li>Food: ${result.food_type}</li>
                                    <li>Temperature: ${result.temperature_c}°C</li>
                                    <li>Humidity: ${result.humidity_percent}%</li>
                                    <li>Gas: ${result.gas_ppm} ppm</li>
                                    <li>Days: ${result.day}</li>
                                </ul>
                                <p><strong>Prediction:</strong></p>
                                <p><strong>Status:</strong> <span style="color: ${result.freshness_percentage > 70 ? '#28a745' : result.freshness_percentage > 30 ? '#ffc107' : '#dc3545'}; font-size: 1.2em; font-weight: bold;">${result.status.toUpperCase()}</span></p>
                                <p><strong>Freshness:</strong> ${result.freshness_percentage.toFixed(1)}%</p>
                                <p><strong>Remaining Days:</strong> ${result.remaining_days.toFixed(1)}</p>
                                <p><strong>Confidence:</strong> ${(result.confidence * 100).toFixed(1)}%</p>
                                <p><strong>Spoiled Probability:</strong> ${(result.spoiled_probability * 100).toFixed(1)}%</p>
                            `;
                            
                        } catch (error) {
                            responseBox.style.display = 'block';
                            responseBox.style.background = '#f8d7da';
                            responseBox.style.borderColor = '#f5c6cb';
                            responseBox.innerHTML = `<h3>❌ Error</h3><p>${error.message}</p>`;
                        }
                        
                        button.textContent = '🔮 Predict Freshness';
                        button.disabled = false;
                    });
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            
        elif self.path == '/model/info':
            self.send_json_response(model.get_model_info())
            
        elif self.path == '/health':
            self.send_json_response({
                'status': 'healthy',
                'model_loaded': True,
                'api_type': 'SimpleHTTP'
            })
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_POST(self):
        if self.path == '/predict':
            try:
                # Read the request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Parse JSON
                data = json.loads(post_data.decode('utf-8'))
                
                # Validate required fields
                required_fields = ['food_type', 'temperature_c', 'humidity_percent', 'gas_ppm', 'day']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.send_json_response({
                        'error': f'Missing required fields: {missing_fields}'
                    }, 400)
                    return
                
                # Make prediction
                prediction = model.predict(
                    food_type=data['food_type'],
                    temperature_c=float(data['temperature_c']),
                    humidity_percent=float(data['humidity_percent']),
                    gas_ppm=float(data['gas_ppm']),
                    day=float(data['day'])
                )
                
                self.send_json_response(prediction)
                
            except json.JSONDecodeError:
                self.send_json_response({'error': 'Invalid JSON'}, 400)
            except Exception as e:
                self.send_json_response({'error': str(e)}, 500)
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # CORS
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server(port=9000):
    """Run the HTTP server"""
    handler = FoodAPIHandler
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🚀 Food Freshness API Server Started!")
        print(f"🌐 Server running at: http://localhost:{port}")
        print(f"📖 API docs: http://localhost:{port}")
        print(f"❤️  Health check: http://localhost:{port}/health")
        print(f"🧠 Model info: http://localhost:{port}/model/info")
        print(f"🛑 Press Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")

if __name__ == "__main__":
    run_server()
