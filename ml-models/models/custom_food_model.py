import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
import joblib
import logging
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

class CustomFoodModel:
    """
    Custom ML model for food freshness monitoring with specific dataset columns:
    1. food_type
    2. temperature_c
    3. humidity_percent
    4. gas_ppm
    5. day
    6. spoiled
    7. remaining_days
    """
    
    def __init__(self):
        self.food_type_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.spoilage_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.shelf_life_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
        
        self.is_trained = False
        self.feature_names = []
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def preprocess_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Preprocess the dataset with specific columns.
        """
        self.logger.info("Preprocessing data...")
        
        # Make a copy to avoid modifying original
        df_processed = df.copy()
        
        # Encode food_type
        df_processed['food_type_encoded'] = self.food_type_encoder.fit_transform(df_processed['food_type'])
        
        # Select features for training
        feature_columns = ['food_type_encoded', 'temperature_c', 'humidity_percent', 'gas_ppm', 'day']
        X = df_processed[feature_columns].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Targets
        y_spoiled = df_processed['spoiled'].values
        y_remaining_days = df_processed['remaining_days'].values
        
        # Store feature names
        self.feature_names = ['food_type', 'temperature_c', 'humidity_percent', 'gas_ppm', 'day']
        
        self.logger.info(f"Preprocessed {len(df_processed)} samples with {len(feature_columns)} features")
        
        return X_scaled, y_spoiled, y_remaining_days
    
    def train(self, df: pd.DataFrame, test_size: float = 0.2) -> Dict[str, Any]:
        """
        Train both spoilage classification and shelf life regression models.
        """
        self.logger.info("Starting model training...")
        
        # Preprocess data
        X, y_spoiled, y_remaining_days = self.preprocess_data(df)
        
        # Split data
        X_train, X_test, y_spoiled_train, y_spoiled_test, y_days_train, y_days_test = train_test_split(
            X, y_spoiled, y_remaining_days, test_size=test_size, random_state=42
        )
        
        # Train spoilage classifier
        self.logger.info("Training spoilage classifier...")
        self.spoilage_classifier.fit(X_train, y_spoiled_train)
        
        # Train shelf life regressor
        self.logger.info("Training shelf life regressor...")
        self.shelf_life_regressor.fit(X_train, y_days_train)
        
        # Evaluate models
        spoiled_pred = self.spoilage_classifier.predict(X_test)
        days_pred = self.shelf_life_regressor.predict(X_test)
        
        # Calculate metrics
        spoilage_accuracy = accuracy_score(y_spoiled_test, spoiled_pred)
        days_rmse = np.sqrt(mean_squared_error(y_days_test, days_pred))
        days_r2 = r2_score(y_days_test, days_pred)
        
        self.is_trained = True
        
        training_results = {
            'spoilage_accuracy': spoilage_accuracy,
            'shelf_life_rmse': days_rmse,
            'shelf_life_r2': days_r2,
            'classification_report': classification_report(y_spoiled_test, spoiled_pred, output_dict=True),
            'feature_importance_spoilage': dict(zip(self.feature_names, self.spoilage_classifier.feature_importances_)),
            'feature_importance_shelf_life': dict(zip(self.feature_names, self.shelf_life_regressor.feature_importances_))
        }
        
        self.logger.info(f"Training completed - Spoilage Accuracy: {spoilage_accuracy:.4f}, Shelf Life RMSE: {days_rmse:.4f}")
        
        return training_results
    
    def predict(self, food_type: str, temperature_c: float, humidity_percent: float, 
                gas_ppm: float, day: int) -> Dict[str, Any]:
        """
        Make predictions for new data.
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Create input array
        try:
            food_type_encoded = self.food_type_encoder.transform([food_type])[0]
        except ValueError:
            # Handle unknown food types
            food_type_encoded = 0  # Default to first known food type
            self.logger.warning(f"Unknown food type '{food_type}', using default")
        
        input_data = np.array([[food_type_encoded, temperature_c, humidity_percent, gas_ppm, day]])
        
        # Scale input
        input_scaled = self.scaler.transform(input_data)
        
        # Make predictions
        spoiled_prob = self.spoilage_classifier.predict_proba(input_scaled)[0]
        spoiled_prediction = self.spoilage_classifier.predict(input_scaled)[0]
        remaining_days = self.shelf_life_regressor.predict(input_scaled)[0]
        
        # Calculate freshness percentage
        freshness_percentage = max(0, min(100, (1 - spoiled_prob[1]) * 100))
        
        # Determine status
        if freshness_percentage >= 80:
            status = "fresh"
        elif freshness_percentage >= 60:
            status = "good"
        elif freshness_percentage >= 40:
            status = "moderate"
        elif freshness_percentage >= 20:
            status = "spoiling"
        else:
            status = "spoiled"
        
        return {
            'food_type': food_type,
            'temperature_c': temperature_c,
            'humidity_percent': humidity_percent,
            'gas_ppm': gas_ppm,
            'day': day,
            'spoiled_prediction': bool(spoiled_prediction),
            'spoiled_probability': float(spoiled_prob[1]),
            'freshness_percentage': float(freshness_percentage),
            'status': status,
            'remaining_days': max(0, float(remaining_days)),
            'confidence': float(max(spoiled_prob))
        }
    
    def predict_batch(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Make batch predictions.
        """
        results = []
        for data in data_list:
            try:
                prediction = self.predict(
                    food_type=data['food_type'],
                    temperature_c=data['temperature_c'],
                    humidity_percent=data['humidity_percent'],
                    gas_ppm=data['gas_ppm'],
                    day=data['day']
                )
                results.append(prediction)
            except Exception as e:
                results.append({'error': str(e), 'input': data})
        
        return results
    
    def save_model(self, filepath: str):
        """
        Save the trained model.
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Cannot save.")
        
        model_data = {
            'food_type_encoder': self.food_type_encoder,
            'scaler': self.scaler,
            'spoilage_classifier': self.spoilage_classifier,
            'shelf_life_regressor': self.shelf_life_regressor,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        
        joblib.dump(model_data, filepath)
        self.logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """
        Load a trained model.
        """
        model_data = joblib.load(filepath)
        
        self.food_type_encoder = model_data['food_type_encoder']
        self.scaler = model_data['scaler']
        self.spoilage_classifier = model_data['spoilage_classifier']
        self.shelf_life_regressor = model_data['shelf_life_regressor']
        self.feature_names = model_data['feature_names']
        self.is_trained = model_data['is_trained']
        
        self.logger.info(f"Model loaded from {filepath}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information and statistics.
        """
        if not self.is_trained:
            return {'error': 'Model not trained'}
        
        return {
            'feature_names': self.feature_names,
            'food_types': list(self.food_type_encoder.classes_),
            'n_features': len(self.feature_names),
            'model_type': 'RandomForest',
            'is_trained': self.is_trained
        }

# Data generator for custom dataset format
class CustomDataGenerator:
    """
    Generate sample data matching the custom dataset format.
    """
    
    def __init__(self, random_seed: int = 42):
        np.random.seed(random_seed)
        
        self.food_types = [
            'leafy_greens', 'fruits', 'vegetables', 'herbs',
            'canned_goods', 'dry_goods', 'frozen_foods', 'snacks',
            'burgers', 'pizza', 'sandwiches', 'fried_items',
            'prepared_meals', 'leftovers', 'restaurant_food', 'homemade'
        ]
        
        # Base shelf life for each food type (in days)
        self.base_shelf_life = {
            'leafy_greens': 5, 'fruits': 7, 'vegetables': 10, 'herbs': 3,
            'canned_goods': 365, 'dry_goods': 180, 'frozen_foods': 365, 'snacks': 90,
            'burgers': 2, 'pizza': 3, 'sandwiches': 2, 'fried_items': 2,
            'prepared_meals': 3, 'leftovers': 3, 'restaurant_food': 3, 'homemade': 4
        }
    
    def generate_sample_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """
        Generate sample data matching the required format.
        """
        data = []
        
        for i in range(n_samples):
            # Random food type
            food_type = np.random.choice(self.food_types)
            base_life = self.base_shelf_life[food_type]
            
            # Random day (0 to base_life * 1.5)
            day = np.random.uniform(0, base_life * 1.5)
            
            # Generate sensor readings based on food type and day
            temp = self._generate_temperature(food_type, day)
            humidity = self._generate_humidity(food_type, day)
            gas = self._generate_gas_ppm(food_type, day)
            
            # Calculate remaining days
            remaining_days = max(0, base_life - day + np.random.normal(0, 0.5))
            
            # Determine if spoiled (based on gas concentration and remaining days)
            spoiled = 1 if (gas > 0.5 or remaining_days < 1) else 0
            
            data.append({
                'food_type': food_type,
                'temperature_c': round(temp, 2),
                'humidity_percent': round(humidity, 2),
                'gas_ppm': round(gas, 3),
                'day': round(day, 1),
                'spoiled': spoiled,
                'remaining_days': round(remaining_days, 1)
            })
        
        return pd.DataFrame(data)
    
    def _generate_temperature(self, food_type: str, day: float) -> float:
        """Generate realistic temperature based on food type and age."""
        optimal_temps = {
            'leafy_greens': 4, 'fruits': 5, 'vegetables': 4, 'herbs': 3,
            'canned_goods': 20, 'dry_goods': 20, 'frozen_foods': -18, 'snacks': 22,
            'burgers': 4, 'pizza': 4, 'sandwiches': 4, 'fried_items': 4,
            'prepared_meals': 4, 'leftovers': 4, 'restaurant_food': 4, 'homemade': 4
        }
        
        base_temp = optimal_temps[food_type]
        # Add variation and increase with age
        temp = base_temp + np.random.normal(0, 2) + (day * 0.1)
        return max(-25, min(40, temp))
    
    def _generate_humidity(self, food_type: str, day: float) -> float:
        """Generate realistic humidity based on food type and age."""
        optimal_humidity = {
            'leafy_greens': 95, 'fruits': 90, 'vegetables': 95, 'herbs': 98,
            'canned_goods': 60, 'dry_goods': 50, 'frozen_foods': 80, 'snacks': 40,
            'burgers': 85, 'pizza': 85, 'sandwiches': 85, 'fried_items': 80,
            'prepared_meals': 85, 'leftovers': 85, 'restaurant_food': 85, 'homemade': 85
        }
        
        base_humidity = optimal_humidity[food_type]
        # Add variation and slight changes with age
        humidity = base_humidity + np.random.normal(0, 5) + (day * 0.2)
        return max(10, min(100, humidity))
    
    def _generate_gas_ppm(self, food_type: str, day: float) -> float:
        """Generate realistic gas concentration based on food type and age."""
        base_gas = 0.1  # Base gas concentration
        
        # Increase with age, faster for perishable items
        if food_type in ['burgers', 'leafy_greens', 'prepared_meals']:
            gas_rate = 0.15
        elif food_type in ['canned_goods', 'dry_goods', 'frozen_foods']:
            gas_rate = 0.02
        else:
            gas_rate = 0.08
        
        gas = base_gas + (day * gas_rate) + np.random.normal(0, 0.05)
        return max(0, min(2.0, gas))

# Example usage and training script
def train_custom_model(data_path: str = None, n_samples: int = 5000):
    """
    Train the custom model with your dataset format.
    """
    # Initialize model and data generator
    model = CustomFoodModel()
    generator = CustomDataGenerator()
    
    # Load or generate data
    if data_path and os.path.exists(data_path):
        print(f"Loading data from {data_path}")
        df = pd.read_csv(data_path)
    else:
        print(f"Generating {n_samples} sample samples...")
        df = generator.generate_sample_data(n_samples)
        # Save generated data
        df.to_csv('custom_food_data.csv', index=False)
        print("Sample data saved to 'custom_food_data.csv'")
    
    # Train model
    print("Training model...")
    results = model.train(df)
    
    # Save model
    model.save_model('custom_food_model.pkl')
    print("Model saved to 'custom_food_model.pkl'")
    
    # Print results
    print("\nTraining Results:")
    print(f"Spoilage Accuracy: {results['spoilage_accuracy']:.4f}")
    print(f"Shelf Life RMSE: {results['shelf_life_rmse']:.4f} days")
    print(f"Shelf Life R²: {results['shelf_life_r2']:.4f}")
    
    return model, results

if __name__ == "__main__":
    import os
    
    # Train the model
    model, results = train_custom_model()
    
    # Test with sample prediction
    print("\nSample Prediction:")
    prediction = model.predict(
        food_type='leafy_greens',
        temperature_c=4.5,
        humidity_percent=85.0,
        gas_ppm=0.3,
        day=2
    )
    print(prediction)
