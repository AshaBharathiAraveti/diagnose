#!/usr/bin/env python3
"""
Simple prediction script for your custom food model.
No Flask required - just direct predictions.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from models.custom_food_model import CustomFoodModel

def load_model():
    """Load the trained model"""
    model = CustomFoodModel()
    model_file = "custom_food_model.pkl"
    
    if os.path.exists(model_file):
        model.load_model(model_file)
        print("✅ Model loaded successfully")
        return model
    else:
        print(f"❌ Model file '{model_file}' not found. Please train the model first.")
        print("Run: python train_custom_model.py")
        return None

def predict_single(model, food_type, temperature_c, humidity_percent, gas_ppm, day):
    """Make a single prediction"""
    try:
        prediction = model.predict(
            food_type=food_type,
            temperature_c=float(temperature_c),
            humidity_percent=float(humidity_percent),
            gas_ppm=float(gas_ppm),
            day=float(day)
        )
        return prediction
    except Exception as e:
        return {'error': str(e)}

def predict_from_csv_row(model, csv_row):
    """Predict from a CSV row string"""
    try:
        # Parse CSV row: food_type,temperature_c,humidity_percent,gas_ppm,day,spoiled,remaining_days
        parts = csv_row.strip().split(',')
        if len(parts) >= 5:
            food_type = parts[0].strip()
            temperature_c = float(parts[1].strip())
            humidity_percent = float(parts[2].strip())
            gas_ppm = float(parts[3].strip())
            day = float(parts[4].strip())
            
            return predict_single(model, food_type, temperature_c, humidity_percent, gas_ppm, day)
        else:
            return {'error': 'Invalid CSV format'}
    except Exception as e:
        return {'error': str(e)}

def interactive_prediction(model):
    """Interactive prediction mode"""
    print("\n🍎 Interactive Food Freshness Prediction")
    print("=" * 50)
    print("Enter 'quit' to exit\n")
    
    while True:
        try:
            print("Enter food details:")
            food_type = input("Food type (e.g., leafy_greens, burgers, canned_goods): ").strip()
            if food_type.lower() == 'quit':
                break
            
            temperature_c = input("Temperature (°C): ").strip()
            if temperature_c.lower() == 'quit':
                break
            temperature_c = float(temperature_c)
            
            humidity_percent = input("Humidity (%): ").strip()
            if humidity_percent.lower() == 'quit':
                break
            humidity_percent = float(humidity_percent)
            
            gas_ppm = input("Gas concentration (ppm): ").strip()
            if gas_ppm.lower() == 'quit':
                break
            gas_ppm = float(gas_ppm)
            
            day = input("Days since storage: ").strip()
            if day.lower() == 'quit':
                break
            day = float(day)
            
            # Make prediction
            prediction = predict_single(model, food_type, temperature_c, humidity_percent, gas_ppm, day)
            
            if 'error' in prediction:
                print(f"❌ Error: {prediction['error']}")
            else:
                print(f"\n🔍 Prediction Results:")
                print(f"🍎 Food: {prediction['food_type']}")
                print(f"🌡️  Temperature: {prediction['temperature_c']}°C")
                print(f"💧 Humidity: {prediction['humidity_percent']}%")
                print(f"💨 Gas: {prediction['gas_ppm']} ppm")
                print(f"📅 Days: {prediction['day']}")
                print(f"-" * 30)
                print(f"📊 Status: {prediction['status'].upper()}")
                print(f"📈 Freshness: {prediction['freshness_percentage']:.1f}%")
                print(f"⚠️  Spoiled Probability: {prediction['spoiled_probability']:.3f}")
                print(f"⏰ Remaining Days: {prediction['remaining_days']:.1f}")
                print(f"🎯 Confidence: {prediction['confidence']:.3f}")
                print(f"-" * 30)
            
            print("\n" + "="*50 + "\n")
            
        except KeyboardInterrupt:
            break
        except ValueError as e:
            print(f"❌ Invalid input: {e}")
            print("Please enter valid numbers.\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")

def batch_prediction(model, csv_file):
    """Batch prediction from CSV file"""
    try:
        with open(csv_file, 'r') as f:
            lines = f.readlines()
        
        print(f"\n📊 Processing {len(lines)} samples from {csv_file}")
        print("=" * 60)
        
        correct_predictions = 0
        total_predictions = 0
        
        for i, line in enumerate(lines, 1):
            if line.strip():
                prediction = predict_from_csv_row(model, line)
                
                if 'error' in prediction:
                    print(f"❌ Line {i}: {prediction['error']}")
                    continue
                
                # Extract actual values from CSV for comparison
                parts = line.strip().split(',')
                if len(parts) >= 7:
                    actual_spoiled = int(parts[5].strip())
                    actual_remaining = float(parts[6].strip())
                    
                    # Check if prediction matches actual
                    predicted_spoiled = 1 if prediction['spoiled_prediction'] else 0
                    
                    if predicted_spoiled == actual_spoiled:
                        correct_predictions += 1
                    
                    total_predictions += 1
                    
                    # Show result
                    status = "✅" if predicted_spoiled == actual_spoiled else "❌"
                    print(f"{status} Line {i}: {prediction['food_type']} - "
                          f"Predicted: {prediction['status']} ({prediction['freshness_percentage']:.1f}%), "
                          f"Actual: {'SPOILED' if actual_spoiled else 'FRESH'}")
        
        if total_predictions > 0:
            accuracy = (correct_predictions / total_predictions) * 100
            print(f"\n📈 Batch Results:")
            print(f"✅ Correct predictions: {correct_predictions}/{total_predictions}")
            print(f"🎯 Accuracy: {accuracy:.2f}%")
        
    except FileNotFoundError:
        print(f"❌ File '{csv_file}' not found")
    except Exception as e:
        print(f"❌ Error processing file: {e}")

def show_model_info(model):
    """Show model information"""
    info = model.get_model_info()
    print(f"\n📋 Model Information:")
    print(f"🍎 Supported food types ({len(info['food_types'])}):")
    for food_type in info['food_types']:
        print(f"  - {food_type}")
    print(f"🔧 Features: {', '.join(info['feature_names'])}")
    print(f"🤖 Model type: {info['model_type']}")

def main():
    """Main function"""
    print("🍎 Custom Food Freshness Prediction System")
    print("=" * 50)
    
    # Load model
    model = load_model()
    if model is None:
        return
    
    # Show model info
    show_model_info(model)
    
    print("\n🚀 Choose an option:")
    print("1. Interactive prediction")
    print("2. Batch prediction from CSV")
    print("3. Test with sample data")
    print("4. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            interactive_prediction(model)
        elif choice == '2':
            csv_file = input("Enter CSV file path (default: sample_food_data.csv): ").strip()
            if not csv_file:
                csv_file = "sample_food_data.csv"
            batch_prediction(model, csv_file)
        elif choice == '3':
            print("\n🧪 Testing with sample predictions:")
            test_samples = [
                {'food_type': 'leafy_greens', 'temperature_c': 4.5, 'humidity_percent': 85.0, 'gas_ppm': 0.2, 'day': 1},
                {'food_type': 'burgers', 'temperature_c': 5.0, 'humidity_percent': 80.0, 'gas_ppm': 0.8, 'day': 3},
                {'food_type': 'canned_goods', 'temperature_c': 20.0, 'humidity_percent': 60.0, 'gas_ppm': 0.1, 'day': 100},
            ]
            
            for i, sample in enumerate(test_samples, 1):
                prediction = predict_single(model, **sample)
                if 'error' not in prediction:
                    print(f"\nSample {i}:")
                    print(f"🍎 {prediction['food_type']} - {prediction['status'].upper()}")
                    print(f"📈 Freshness: {prediction['freshness_percentage']:.1f}%")
                    print(f"⏰ Remaining: {prediction['remaining_days']:.1f} days")
                    print(f"🎯 Confidence: {prediction['confidence']:.3f}")
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main()
