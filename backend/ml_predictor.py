"""
ML Integration Module for Food Freshness Monitoring System
Integrates the trained ML models with the Flask backend
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

# Add ML integration directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml_integration'))

class MLPredictor:
    """Handles ML predictions for food freshness monitoring"""
    
    def __init__(self):
        self.model = None
        self.is_loaded = False
        self.logger = logging.getLogger(__name__)
        
        # Try to load the trained model
        self._load_model()
    
    def _load_model(self):
        """Load the trained ML model"""
        try:
            model_path = os.path.join(os.path.dirname(__file__), 'custom_food_model.pkl')
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                # Check if it's the expected dictionary structure
                if isinstance(self.model, dict) and 'spoilage_classifier' in self.model:
                    self.is_loaded = True
                    self.logger.info("ML model loaded successfully")
                else:
                    self.logger.error("Model file does not contain expected structure")
                    self.model = None
                    self.is_loaded = False
            else:
                self.logger.warning("ML model file not found")
        except Exception as e:
            self.logger.error(f"Error loading ML model: {str(e)}")
            self.model = None
            self.is_loaded = False
    
    def predict_freshness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a freshness prediction using the ML model
        
        Args:
            data: Dictionary containing sensor data and food information
            
        Returns:
            Dictionary with prediction results
        """
        if not self.is_loaded:
            return {
                "success": False,
                "error": "ML model not loaded",
                "fallback_prediction": self._fallback_prediction(data)
            }
        
        try:
            # Prepare data for prediction
            input_data = self._prepare_input_data(data)
            
            # Make prediction using the correct model components
            classifier = self.model['spoilage_classifier']
            regressor = self.model['shelf_life_regressor']
            
            if hasattr(classifier, 'predict') and hasattr(regressor, 'predict'):
                # Use numpy array to suppress sklearn feature-name warnings
                input_values = input_data.values

                # Predict freshness status
                freshness_prediction = classifier.predict(input_values)[0]
                confidence = self._get_confidence(input_values, classifier)

                # Predict remaining days
                days_prediction = regressor.predict(input_values)[0]

                return {
                    "success": True,
                    "predicted_status": self._map_prediction_to_status(freshness_prediction),
                    "confidence": confidence,
                    "freshness_percentage": self._calculate_freshness_percentage(freshness_prediction, confidence),
                    "predicted_remaining_days": float(days_prediction),
                    "recommendations": self._generate_recommendations(data, freshness_prediction)
                }
            else:
                return {
                    "success": False,
                    "error": "Model components don't have predict method",
                    "fallback_prediction": self._fallback_prediction(data)
                }
                
        except Exception as e:
            self.logger.error(f"Prediction error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_prediction": self._fallback_prediction(data)
            }
    
    def _prepare_input_data(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare input data for ML model"""
        # Map incoming data to expected format
        mapped_data = {
            'food_type': data.get('food_type', 'unknown'),
            'temperature_c': float(data.get('temperature', 25.0)),
            'humidity_percent': float(data.get('humidity', 60.0)),
            'gas_ppm': float(data.get('gas', 0.5)),
            'day': 1  # Default day, could be calculated from timestamp
        }
        
        df = pd.DataFrame([mapped_data])
        
        # Apply preprocessing using the model's components
        try:
            # Encode food type with fallback for unknown types
            food_type_encoder = self.model['food_type_encoder']
            food_type = df['food_type'].iloc[0]
            known_classes = list(food_type_encoder.classes_)

            if food_type in known_classes:
                df['food_type_encoded'] = food_type_encoder.transform([food_type])[0]
            else:
                # Map unknown food types to closest KNOWN category.
                # The fallback must itself exist in known_classes.
                food_type_mapping = {
                    'dairy':    'fruits',
                    'meat':     'fruits',
                    'fish':     'fruits',
                    'cooked':   'fruits',
                    'packaged': 'fruits',
                    'vegetables': 'fruits',  # in case vegetables isn't trained
                }
                # Try mapping, then try first known class, then 0
                mapped_type = food_type_mapping.get(food_type, None)
                if mapped_type not in known_classes:
                    mapped_type = known_classes[0] if known_classes else None

                if mapped_type:
                    df['food_type_encoded'] = food_type_encoder.transform([mapped_type])[0]
                    self.logger.warning(f"Unknown food type '{food_type}' mapped to '{mapped_type}'")
                else:
                    df['food_type_encoded'] = 0

            # Select features that match the model's training
            features_df = df[['food_type_encoded', 'temperature_c', 'humidity_percent', 'gas_ppm', 'day']]

            # Scale features
            scaler = self.model['scaler']
            # Pass numpy array to avoid sklearn feature-name warnings
            scaled_features = scaler.transform(features_df.values)

            return pd.DataFrame(scaled_features, columns=['food_type_encoded', 'temperature_c', 'humidity_percent', 'gas_ppm', 'day'])
        except Exception as e:
            self.logger.error(f"Data preprocessing error: {str(e)}")
            # Fallback to basic features without preprocessing
            df['food_type_encoded'] = 0
            return df[['food_type_encoded', 'temperature_c', 'humidity_percent', 'gas_ppm', 'day']]
    
    def _map_prediction_to_status(self, prediction) -> str:
        """Map numerical prediction to status string.
        The spoilage classifier predicts 1=spoiled, 0=not spoiled.
        For display we convert to qualitative status using confidence.
        """
        try:
            val = float(prediction)
        except (TypeError, ValueError):
            return str(prediction)

        # Binary output: 1 = spoiled, 0 = fresh
        if val >= 0.9:
            return "spoiled"
        elif val >= 0.7:
            return "spoiling"
        elif val >= 0.5:
            return "moderate"
        elif val >= 0.2:
            return "good"
        else:
            return "fresh"
    
    def _calculate_freshness_percentage(self, prediction, confidence: float) -> float:
        """Calculate freshness percentage from the classifier output.
        The model predicts spoilage probability (0=fresh, 1=spoiled).
        Freshness % = inverted spoilage probability, scaled by confidence.
        """
        try:
            val = float(prediction)
        except (TypeError, ValueError):
            return 75.0

        # If binary (0 or 1), use confidence as the fresh probability
        if val == 0:
            return min(100.0, max(0.0, confidence * 100))
        elif val == 1:
            return min(100.0, max(0.0, (1.0 - confidence) * 100))
        else:
            # Continuous prediction: invert spoilage prob
            freshness = (1.0 - val) * 100
            return min(100.0, max(0.0, freshness))
    
    def _estimate_remaining_days(self, data: Dict[str, Any], prediction) -> float:
        """Estimate remaining shelf life"""
        food_type = data.get('food_type', 'unknown')
        temperature = float(data.get('temperature', 25.0))
        
        # Base shelf life by food type (days)
        base_shelf_life = {
            'leafy_greens': 5,
            'fruits': 7,
            'vegetables': 10,
            'herbs': 4,
            'dairy': 14,
            'meat': 7,
            'fish': 3,
            'cooked': 5,
            'packaged': 30,
            'unknown': 7
        }
        
        base_days = base_shelf_life.get(food_type, 7)
        
        # Temperature adjustment
        if temperature < 5:  # Refrigerated
            temp_factor = 1.5
        elif temperature < 15:  # Cool
            temp_factor = 1.0
        elif temperature < 25:  # Room temperature
            temp_factor = 0.7
        else:  # Warm
            temp_factor = 0.4
        
        # Adjust by prediction
        if isinstance(prediction, (int, float)):
            prediction_factor = prediction
        else:
            prediction_factor = 0.7
        
        estimated_days = base_days * temp_factor * prediction_factor
        return max(0.1, estimated_days)
    
    def _generate_recommendations(self, data: Dict[str, Any], prediction) -> Dict[str, Any]:
        """Generate storage recommendations"""
        food_type = data.get('food_type', 'unknown')
        temperature = float(data.get('temperature', 25.0))
        humidity = float(data.get('humidity', 60.0))
        
        recommendations = []
        
        # Temperature recommendations
        if temperature > 10:
            recommendations.append("Consider refrigeration to extend shelf life")
        elif temperature < 2:
            recommendations.append("Temperature too low - may cause freezing damage")
        
        # Humidity recommendations
        if humidity < 40:
            recommendations.append("Increase humidity to prevent drying")
        elif humidity > 80:
            recommendations.append("Reduce humidity to prevent mold growth")
        
        # Food-specific recommendations
        if food_type in ['leafy_greens', 'herbs']:
            recommendations.append("Store in airtight container with paper towel")
        elif food_type in ['fruits']:
            recommendations.append("Keep away from vegetables to prevent ripening")
        
        return {
            "food_type": food_type,
            "recommendations": recommendations,
            "optimal_conditions": {
                "temperature": 4.0,
                "humidity": 70.0
            }
        }
    
    def _get_confidence(self, input_data, classifier) -> float:
        """Get prediction confidence if available"""
        try:
            if hasattr(classifier, 'predict_proba'):
                probabilities = classifier.predict_proba(input_data)
                return float(np.max(probabilities))
        except:
            pass
        return 0.8  # Default confidence
    
    def _fallback_prediction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback prediction when ML model is not available"""
        temperature = float(data.get('temperature', 25.0))
        humidity = float(data.get('humidity', 60.0))
        gas = float(data.get('gas', 0.5))
        
        # Simple rule-based prediction
        if temperature > 25 or gas > 1.0:
            status = "spoiling"
            freshness = 30.0
            days = 2.0
        elif temperature > 15 or gas > 0.7:
            status = "moderate"
            freshness = 60.0
            days = 5.0
        else:
            status = "fresh"
            freshness = 85.0
            days = 7.0
        
        return {
            "predicted_status": status,
            "confidence": 0.6,
            "freshness_percentage": freshness,
            "predicted_remaining_days": days,
            "recommendations": self._generate_recommendations(data, status)
        }
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get the current status of the ML model"""
        return {
            "is_loaded": self.is_loaded,
            "model_available": os.path.exists(os.path.join(os.path.dirname(__file__), 'custom_food_model.pkl')),
            "fallback_available": True
        }

# Global instance
ml_predictor = MLPredictor()
