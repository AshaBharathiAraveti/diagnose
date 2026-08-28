"""
Real-time Food Freshness Monitoring System
Dynamic sensor values, continuous ML predictions, and live analytics
"""

import time
import random
import threading
import requests
import json
from datetime import datetime
import sqlite3

class DynamicFoodMonitor:
    def __init__(self):
        self.running = False
        self.sensor_data = {}
        self.prediction_history = []
        self.analytics_data = {
            'status_counts': {},
            'confidence_trends': [],
            'food_type_stats': {},
            'temp_impact': []
        }
        
        # Base sensor values for different food types
        self.base_values = {
            'leafy_greens': {'temp': 4.0, 'humidity': 85.0, 'gas': 0.3, 'spoilage_rate': 0.1},
            'dairy': {'temp': 5.0, 'humidity': 70.0, 'gas': 0.4, 'spoilage_rate': 0.05},
            'meat': {'temp': 2.0, 'humidity': 80.0, 'gas': 0.8, 'spoilage_rate': 0.15},
            'fruits': {'temp': 8.0, 'humidity': 75.0, 'gas': 0.5, 'spoilage_rate': 0.08},
            'vegetables': {'temp': 6.0, 'humidity': 65.0, 'gas': 0.2, 'spoilage_rate': 0.06}
        }
        
    def get_dynamic_sensor_values(self, food_type):
        """Generate realistic dynamic sensor values"""
        if food_type not in self.base_values:
            food_type = 'leafy_greens'
            
        base = self.base_values[food_type]
        current_time = time.time()
        
        # Time-based variations
        hour_factor = (current_time % 86400) / 86400  # 0-1 throughout the day
        day_factor = (current_time % 604800) / 604800  # 0-1 throughout the week
        
        # Temperature fluctuates based on time of day
        temp_variation = math.sin(hour_factor * 2 * math.pi) * 3.0
        
        # Humidity and gas increase over time (spoilage simulation)
        spoilage_factor = 1 + (day_factor * base['spoilage_rate'] * 10)
        gas_increase = base['gas'] * spoilage_factor
        
        # Random environmental factors
        random_factor = random.uniform(0.95, 1.05)
        
        return {
            'temperature': round(base['temp'] + temp_variation, 1),
            'humidity': round(max(0, min(100, base['humidity'] * random_factor)), 1),
            'gas': round(base['gas'] + gas_increase, 2),
            'timestamp': datetime.now().isoformat()
        }
    
    def make_prediction(self, food_type):
        """Make ML prediction and update analytics"""
        try:
            sensor_values = self.get_dynamic_sensor_values(food_type)
            
            # Prepare data for ML prediction
            data = {
                'food_type': food_type,
                'temperature': sensor_values['temperature'],
                'humidity': sensor_values['humidity'],
                'gas': sensor_values['gas']
            }
            
            # Make prediction
            response = requests.post('http://localhost:5000/api/predict/freshness', 
                                   json=data, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success') and result.get('data', {}).get('success', False):
                    prediction_data = result['data']
                    
                    # Store in database
                    self.store_prediction(food_type, sensor_values, prediction_data)
                    
                    # Update analytics
                    self.update_analytics(food_type, prediction_data)
                    
                    # Display results
                    self.display_realtime_results(food_type, sensor_values, prediction_data)
                    
                    return True
                else:
                    print(f"❌ ML Prediction failed: {result.get('data', {}).get('error', 'Unknown')}")
                    return False
            else:
                print(f"❌ Server error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Prediction error: {str(e)}")
            return False
    
    def store_prediction(self, food_type, sensor_values, prediction_data):
        """Store prediction in database"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO food_freshness
                (food_type, temperature, humidity, gas, spoiled, remaining_days, freshness_percent, 
                 ml_predicted_status, ml_confidence, ml_predicted_days, ml_freshness_percentage, 
                 ml_recommendations, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                food_type,
                sensor_values['temperature'],
                sensor_values['humidity'],
                sensor_values['gas'],
                1 if prediction_data.get('predicted_status') in ['spoiled', 'spoiling'] else 0,
                prediction_data.get('predicted_remaining_days', 0),
                prediction_data.get('freshness_percentage', 0),
                prediction_data.get('predicted_status', ''),
                prediction_data.get('confidence', 0),
                prediction_data.get('predicted_remaining_days', 0),
                prediction_data.get('freshness_percentage', 0),
                str(prediction_data.get('recommendations', {})),
                sensor_values['timestamp']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Database error: {str(e)}")
    
    def update_analytics(self, food_type, prediction_data):
        """Update analytics data"""
        # Status counts
        status = prediction_data.get('predicted_status', 'unknown')
        self.analytics_data['status_counts'][status] = self.analytics_data['status_counts'].get(status, 0) + 1
        
        # Confidence trends
        confidence = prediction_data.get('confidence', 0)
        self.analytics_data['confidence_trends'].append({
            'timestamp': datetime.now().isoformat(),
            'confidence': confidence,
            'food_type': food_type
        })
        
        # Keep only last 100 confidence readings
        if len(self.analytics_data['confidence_trends']) > 100:
            self.analytics_data['confidence_trends'] = self.analytics_data['confidence_trends'][-100:]
        
        # Food type statistics
        if food_type not in self.analytics_data['food_type_stats']:
            self.analytics_data['food_type_stats'][food_type] = {
                'predictions': 0,
                'avg_confidence': 0,
                'avg_freshness': 0
            }
        
        stats = self.analytics_data['food_type_stats'][food_type]
        stats['predictions'] += 1
        stats['avg_confidence'] = (stats['avg_confidence'] + confidence) / 2
        stats['avg_freshness'] = (stats['avg_freshness'] + prediction_data.get('freshness_percentage', 0)) / 2
    
    def display_realtime_results(self, food_type, sensor_values, prediction_data):
        """Display real-time prediction results"""
        status = prediction_data.get('predicted_status', 'unknown')
        confidence = prediction_data.get('confidence', 0)
        freshness = prediction_data.get('freshness_percentage', 0)
        days = prediction_data.get('predicted_remaining_days', 0)
        
        # Status color coding
        status_emoji = {
            'fresh': '🟢', 'good': '🟡', 'moderate': '🟠',
            'spoiling': '🟠', 'spoiled': '🔴'
        }.get(status, '⚪')
        
        print(f"\n{status_emoji} {food_type.upper()} - {status.upper()}")
        print(f"🌡 Temp: {sensor_values['temperature']}°C | 💧 Humidity: {sensor_values['humidity']}% | 💨 Gas: {sensor_values['gas']}ppm")
        print(f"📊 Confidence: {confidence:.1%} | 🥬 Freshness: {freshness:.1f}% | ⏰ Days: {days:.1f}")
        print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 60)
    
    def start_continuous_monitoring(self, food_types, interval=3):
        """Start continuous monitoring for multiple food types"""
        self.running = True
        print(f"🚀 Starting real-time monitoring for: {', '.join(food_types)}")
        print(f"⏱️ Update interval: {interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        def monitoring_loop():
            while self.running:
                for food_type in food_types:
                    self.make_prediction(food_type)
                time.sleep(interval)
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitoring_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring...")
            self.running = False
    
    def display_analytics_summary(self):
        """Display analytics summary"""
        print(f"\n📈 ANALYTICS SUMMARY")
        print("=" * 50)
        
        # Status distribution
        print(f"\n🎯 Status Distribution:")
        for status, count in self.analytics_data['status_counts'].items():
            print(f"  {status}: {count}")
        
        # Food type statistics
        print(f"\n🍽 Food Type Performance:")
        for food_type, stats in self.analytics_data['food_type_stats'].items():
            print(f"  {food_type}: {stats['predictions']} predictions, "
                  f"Avg Confidence: {stats['avg_confidence']:.2f}, "
                  f"Avg Freshness: {stats['avg_freshness']:.1f}%")
        
        # Recent confidence trends
        if self.analytics_data['confidence_trends']:
            recent_confidences = [item['confidence'] for item in self.analytics_data['confidence_trends'][-10:]]
            if recent_confidences:
                avg_confidence = sum(recent_confidences) / len(recent_confidences)
                print(f"\n📊 Recent Average Confidence: {avg_confidence:.2f}")

def main():
    monitor = DynamicFoodMonitor()
    
    print("=== Dynamic Food Freshness Monitor ===")
    print("1. Real-time monitoring")
    print("2. Continuous predictions")
    print("3. Live analytics")
    print("4. Database storage")
    
    food_types = input("Enter food types (comma-separated, e.g., leafy_greens,dairy,meat): ").strip()
    if not food_types:
        food_types = ['leafy_greens']
    
    food_types = [ft.strip() for ft in food_types.split(',') if ft.strip()]
    
    interval = input("Update interval in seconds (default 3): ").strip()
    interval = int(interval) if interval.isdigit() else 3
    
    print(f"\n🎯 Starting with {len(food_types)} food types")
    
    try:
        monitor.start_continuous_monitoring(food_types, interval)
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
    finally:
        monitor.display_analytics_summary()

if __name__ == "__main__":
    import math
    main()
