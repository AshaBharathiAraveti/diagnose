"""
Real-time Sensor Data Simulator for Food Freshness Monitoring
Simulates dynamic sensor values that change over time
"""

import time
import random
import threading
import requests
import json

class SensorSimulator:
    def __init__(self):
        self.base_values = {
            'leafy_greens': {'temp': 4.0, 'humidity': 85.0, 'gas': 0.3},
            'dairy': {'temp': 5.0, 'humidity': 70.0, 'gas': 0.4},
            'meat': {'temp': 2.0, 'humidity': 80.0, 'gas': 0.8},
            'fruits': {'temp': 8.0, 'humidity': 75.0, 'gas': 0.5}
        }
        self.current_values = {}
        self.running = False
        
    def get_dynamic_values(self, food_type):
        """Generate dynamic sensor values with realistic variations"""
        if food_type not in self.base_values:
            food_type = 'leafy_greens'
            
        base = self.base_values[food_type]
        
        # Add realistic variations
        temp_variation = random.uniform(-2.0, 3.0)
        humidity_variation = random.uniform(-10.0, 15.0)
        gas_variation = random.uniform(-0.1, 0.3)
        
        # Simulate gradual spoilage (gas increases over time)
        time_factor = time.time() % 1000  # Changes over time
        gas_increase = (time_factor / 1000) * 0.5
        
        return {
            'temperature': round(base['temp'] + temp_variation, 1),
            'humidity': round(max(0, min(100, base['humidity'] + humidity_variation)), 1),
            'gas': round(max(0, base['gas'] + gas_variation + gas_increase), 2)
        }
    
    def send_prediction(self, food_type):
        """Send prediction to API with current sensor values"""
        try:
            values = self.get_dynamic_values(food_type)
            
            data = {
                'food_type': food_type,
                'temperature': values['temperature'],
                'humidity': values['humidity'],
                'gas': values['gas']
            }
            
            response = requests.post('http://localhost:5000/api/predict/freshness', 
                                   json=data, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                print(f"🌡 {food_type}: Temp={values['temperature']}°C, "
                      f"Humidity={values['humidity']}%, Gas={values['gas']}ppm")
                print(f"📊 Status: {result['data'].get('predicted_status', 'N/A')} "
                      f"(Confidence: {result['data'].get('confidence', 0):.2f})")
                print(f"📅 Freshness: {result['data'].get('freshness_percentage', 0):.1f}% | "
                      f"Days left: {result['data'].get('predicted_remaining_days', 0):.1f}")
                print("-" * 60)
            else:
                print(f"❌ Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
    
    def start_continuous_simulation(self, food_types, interval=5):
        """Start continuous simulation for multiple food types"""
        self.running = True
        print(f"🚀 Starting real-time simulation for: {', '.join(food_types)}")
        print(f"📊 Update interval: {interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        def simulation_loop():
            while self.running:
                for food_type in food_types:
                    self.send_prediction(food_type)
                time.sleep(interval)
        
        # Start simulation in background thread
        sim_thread = threading.Thread(target=simulation_loop)
        sim_thread.daemon = True
        sim_thread.start()
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping simulation...")
            self.running = False

def main():
    simulator = SensorSimulator()
    
    print("=== Food Freshness Sensor Simulator ===")
    print("1. Single prediction test")
    print("2. Continuous simulation")
    print("3. Custom food types")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == '1':
        # Single prediction
        food_type = input("Enter food type (leafy_greens, dairy, meat, fruits): ").strip()
        simulator.send_prediction(food_type)
        
    elif choice == '2':
        # Continuous simulation
        food_types = ['leafy_greens', 'dairy', 'meat']
        interval = input("Update interval in seconds (default 5): ").strip()
        interval = int(interval) if interval.isdigit() else 5
        simulator.start_continuous_simulation(food_types, interval)
        
    elif choice == '3':
        # Custom food types
        custom_types = input("Enter food types (comma-separated): ").strip()
        food_types = [ft.strip() for ft in custom_types.split(',') if ft.strip()]
        interval = input("Update interval in seconds (default 5): ").strip()
        interval = int(interval) if interval.isdigit() else 5
        simulator.start_continuous_simulation(food_types, interval)
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
