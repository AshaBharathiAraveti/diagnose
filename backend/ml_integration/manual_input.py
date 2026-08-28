#!/usr/bin/env python3
"""
Manual input testing for your model
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from models.custom_food_model import CustomFoodModel

def manual_test():
    # Load model
    model = CustomFoodModel()
    model.load_model('custom_food_model.pkl')
    
    print("🍎 Manual Input Test")
    print("=" * 30)
    print("Enter your test values (or 'quit' to exit):")
    
    while True:
        try:
            print("\n" + "-" * 30)
            food_type = input("Food type (leafy_greens, burgers, etc.): ").strip()
            if food_type.lower() == 'quit':
                break
                
            temperature = input("Temperature (°C): ").strip()
            if temperature.lower() == 'quit':
                break
            temperature = float(temperature)
            
            humidity = input("Humidity (%): ").strip()
            if humidity.lower() == 'quit':
                break
            humidity = float(humidity)
            
            gas = input("Gas concentration (ppm): ").strip()
            if gas.lower() == 'quit':
                break
            gas = float(gas)
            
            days = input("Days since storage: ").strip()
            if days.lower() == 'quit':
                break
            days = float(days)
            
            # Get prediction
            result = model.predict(food_type, temperature, humidity, gas, days)
            
            print(f"\n🔮 PREDICTION RESULTS:")
            print(f"🍎 Food: {result['food_type']}")
            print(f"📊 Status: {result['status'].upper()}")
            print(f"📈 Freshness: {result['freshness_percentage']:.1f}%")
            print(f"⏰ Remaining Days: {result['remaining_days']:.1f}")
            print(f"🎯 Confidence: {result['confidence']:.3f}")
            print(f"⚠️  Spoiled Probability: {result['spoiled_probability']:.3f}")
            
        except ValueError:
            print("❌ Please enter valid numbers")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    manual_test()
