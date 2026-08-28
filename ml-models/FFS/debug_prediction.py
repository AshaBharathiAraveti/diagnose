#!/usr/bin/env python3
"""
Debug script to understand the specific prediction
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from models.custom_food_model import CustomFoodModel

# Load model
model = CustomFoodModel()
model.load_model('custom_food_model.pkl')

# Test the specific case from your CSV
print("🔍 Testing the specific herbs case:")
print("=" * 50)

# Input from CSV line: herbs,6.29,100.0,0.241,2.4,1,0.5
food_type = "herbs"
temperature_c = 6.29
humidity_percent = 100.0
gas_ppm = 0.241
day = 2.4

print(f"Input:")
print(f"  Food type: {food_type}")
print(f"  Temperature: {temperature_c}°C")
print(f"  Humidity: {humidity_percent}%")
print(f"  Gas: {gas_ppm} ppm")
print(f"  Day: {day}")

print(f"\nActual from CSV:")
print(f"  Spoiled: 1 (SPOILED)")
print(f"  Remaining days: 0.5")

# Make prediction
prediction = model.predict(food_type, temperature_c, humidity_percent, gas_ppm, day)

print(f"\n🔮 Model Prediction:")
print(f"  Status: {prediction['status']}")
print(f"  Freshness: {prediction['freshness_percentage']:.1f}%")
print(f"  Spoiled prediction: {prediction['spoiled_prediction']}")
print(f"  Spoiled probability: {prediction['spoiled_probability']:.3f}")
print(f"  Remaining days: {prediction['remaining_days']:.1f}")
print(f"  Confidence: {prediction['confidence']:.3f}")

# Analysis
print(f"\n📊 Analysis:")
if prediction['spoiled_prediction']:
    print("  Model says: SPOILED")
    actual_spoiled = 1
    if actual_spoiled == 1:
        print("  ✅ Model is CORRECT!")
    else:
        print("  ❌ Model is WRONG!")
else:
    print("  Model says: FRESH")
    actual_spoiled = 1
    if actual_spoiled == 0:
        print("  ✅ Model is CORRECT!")
    else:
        print("  ❌ Model is WRONG!")

# Why this prediction?
print(f"\n🤔 Why this prediction?")
print(f"  Gas concentration {gas_ppm} is relatively low")
print(f"  Day {day} is still early for herbs (base shelf life: 3 days)")
print(f"  Temperature {temperature_c}°C is a bit warm for herbs")
print(f"  Humidity {humidity_percent}% is very high (good for herbs)")

# Check if this makes sense
print(f"\n🧠 Does this make sense?")
print(f"  Herbs typically spoil around day 3+")
print(f"  Gas < 0.3 usually indicates not severely spoiled")
print(f"  But remaining_days = 0.5 suggests it's near end of life")
