#!/usr/bin/env python3
"""
Quick test to get output from your model
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from models.custom_food_model import CustomFoodModel

def test_model():
    # Load the trained model
    model = CustomFoodModel()
    model.load_model('custom_food_model.pkl')
    
    print("🍎 Quick Model Test")
    print("=" * 30)
    
    # Test case 1: Fresh leafy greens
    print("\n🥬 Test 1: Fresh Leafy Greens")
    result1 = model.predict(
        food_type="leafy_greens",
        temperature_c=4.0,
        humidity_percent=95.0,
        gas_ppm=0.1,
        day=1
    )
    print(f"Status: {result1['status']}")
    print(f"Freshness: {result1['freshness_percentage']:.1f}%")
    print(f"Remaining Days: {result1['remaining_days']:.1f}")
    print(f"Confidence: {result1['confidence']:.3f}")
    
    # Test case 2: Spoiling burgers
    print("\n🍔 Test 2: Spoiling Burgers")
    result2 = model.predict(
        food_type="burgers",
        temperature_c=8.0,
        humidity_percent=70.0,
        gas_ppm=0.8,
        day=3
    )
    print(f"Status: {result2['status']}")
    print(f"Freshness: {result2['freshness_percentage']:.1f}%")
    print(f"Remaining Days: {result2['remaining_days']:.1f}")
    print(f"Confidence: {result2['confidence']:.3f}")
    
    # Test case 3: Canned goods
    print("\n🥫 Test 3: Canned Goods")
    result3 = model.predict(
        food_type="canned_goods",
        temperature_c=25.0,
        humidity_percent=60.0,
        gas_ppm=0.05,
        day=200
    )
    print(f"Status: {result3['status']}")
    print(f"Freshness: {result3['freshness_percentage']:.1f}%")
    print(f"Remaining Days: {result3['remaining_days']:.1f}")
    print(f"Confidence: {result3['confidence']:.3f}")

if __name__ == "__main__":
    test_model()
