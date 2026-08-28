#!/usr/bin/env python3
"""
Training script for custom food freshness model with your specific dataset columns.
Dataset columns: food_type, temperature_c, humidity_percent, gas_ppm, day, spoiled, remaining_days
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from models.custom_food_model import CustomFoodModel, CustomDataGenerator

def main():
    """
    Main training script for custom food model.
    """
    print("🍎 Custom Food Freshness Model Training")
    print("=" * 50)
    
    # Initialize model
    model = CustomFoodModel()
    generator = CustomDataGenerator()
    
    # Check for custom data file
    data_file = "your_food_data.csv"  # Change this to your data file path
    
    if os.path.exists(data_file):
        print(f"📁 Loading your data from: {data_file}")
        try:
            df = pd.read_csv(data_file)
            print(f"✅ Loaded {len(df)} samples from your dataset")
            
            # Validate columns
            required_columns = ['food_type', 'temperature_c', 'humidity_percent', 'gas_ppm', 'day', 'spoiled', 'remaining_days']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"❌ Missing required columns: {missing_columns}")
                print(f"Required columns: {required_columns}")
                print("Please ensure your CSV has these exact column names.")
                return
            else:
                print("✅ All required columns found")
                
        except Exception as e:
            print(f"❌ Error loading your data: {e}")
            use_sample = input("Would you like to use sample data instead? (y/n): ")
            if use_sample.lower() != 'y':
                return
            else:
                df = None
    else:
        print(f"📁 Your data file '{data_file}' not found.")
        use_sample = input("Would you like to generate sample data for testing? (y/n): ")
        if use_sample.lower() != 'y':
            print("Please place your CSV file with the required columns and try again.")
            print("Required columns: food_type, temperature_c, humidity_percent, gas_ppm, day, spoiled, remaining_days")
            return
        else:
            df = None
    
    # Generate sample data if needed
    if df is None:
        n_samples = input("How many samples would you like to generate? (default: 5000): ")
        try:
            n_samples = int(n_samples) if n_samples else 5000
        except ValueError:
            n_samples = 5000
        
        print(f"🔄 Generating {n_samples} sample samples...")
        df = generator.generate_sample_data(n_samples)
        
        # Save sample data
        sample_file = "sample_food_data.csv"
        df.to_csv(sample_file, index=False)
        print(f"✅ Sample data saved to: {sample_file}")
        
        # Show sample data
        print("\n📊 Sample data preview:")
        print(df.head())
        print(f"\nData statistics:")
        print(f"- Food types: {df['food_type'].nunique()}")
        print(f"- Temperature range: {df['temperature_c'].min():.1f}°C to {df['temperature_c'].max():.1f}°C")
        print(f"- Humidity range: {df['humidity_percent'].min():.1f}% to {df['humidity_percent'].max():.1f}%")
        print(f"- Gas concentration range: {df['gas_ppm'].min():.3f} to {df['gas_ppm'].max():.3f}")
        print(f"- Spoiled samples: {df['spoiled'].sum()} ({df['spoiled'].mean()*100:.1f}%)")
    
    # Train the model
    print("\n🚀 Starting model training...")
    try:
        results = model.train(df)
        
        print("\n✅ Training completed successfully!")
        print("\n📈 Model Performance:")
        print(f"- Spoilage Detection Accuracy: {results['spoilage_accuracy']:.4f} ({results['spoilage_accuracy']*100:.2f}%)")
        print(f"- Shelf Life Prediction RMSE: {results['shelf_life_rmse']:.4f} days")
        print(f"- Shelf Life Prediction R²: {results['shelf_life_r2']:.4f}")
        
        # Save the model
        model_file = "custom_food_model.pkl"
        model.save_model(model_file)
        print(f"\n💾 Model saved to: {model_file}")
        
        # Show feature importance
        print("\n🔍 Feature Importance (Spoilage Detection):")
        for feature, importance in results['feature_importance_spoilage'].items():
            print(f"- {feature}: {importance:.4f}")
        
        print("\n🔍 Feature Importance (Shelf Life Prediction):")
        for feature, importance in results['feature_importance_shelf_life'].items():
            print(f"- {feature}: {importance:.4f}")
        
        # Test with sample predictions
        print("\n🧪 Sample Predictions:")
        
        test_samples = [
            {'food_type': 'leafy_greens', 'temperature_c': 4.5, 'humidity_percent': 85.0, 'gas_ppm': 0.2, 'day': 1},
            {'food_type': 'burgers', 'temperature_c': 5.0, 'humidity_percent': 80.0, 'gas_ppm': 0.8, 'day': 3},
            {'food_type': 'canned_goods', 'temperature_c': 20.0, 'humidity_percent': 60.0, 'gas_ppm': 0.1, 'day': 100},
        ]
        
        for i, sample in enumerate(test_samples, 1):
            prediction = model.predict(**sample)
            print(f"\nSample {i}:")
            print(f"- Food: {prediction['food_type']}")
            print(f"- Status: {prediction['status'].upper()}")
            print(f"- Freshness: {prediction['freshness_percentage']:.1f}%")
            print(f"- Spoiled Probability: {prediction['spoiled_probability']:.3f}")
            print(f"- Remaining Days: {prediction['remaining_days']:.1f}")
            print(f"- Confidence: {prediction['confidence']:.3f}")
        
        # Show model info
        print(f"\n📋 Model Information:")
        info = model.get_model_info()
        print(f"- Supported food types: {len(info['food_types'])}")
        print(f"- Features: {', '.join(info['feature_names'])}")
        print(f"- Model type: {info['model_type']}")
        
        print(f"\n🎉 Training completed! Your model is ready to use.")
        print(f"📁 Model file: {model_file}")
        print(f"📁 Data file: {data_file if os.path.exists(data_file) else 'sample_food_data.csv'}")
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        print("Please check your data and try again.")
        return

if __name__ == "__main__":
    main()
