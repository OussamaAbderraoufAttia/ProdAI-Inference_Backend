import pickle
import pandas as pd
import numpy as np

class SalesAgent:
    def __init__(self):
        """Initialize SalesAgent and load model."""
        self.model = self.load_model("Igbmr_model.pkl")
    
    def load_model(self, model_path):
        """Load a sales forecasting model."""
        try:
            with open(model_path, "rb") as f:
                model = pickle.load(f)
                if hasattr(model, 'predict'):
                    return model
                else:
                    raise ValueError("Loaded model does not have 'predict' method.")
        except Exception as e:
            print(f"Error loading model: {e}")
            return None

    def handle_request(self, request):
        """Handle different user requests."""
        if "forecast" in request.lower():
            return self.generate_forecast()
        else:
            return "Sales Agent received the request but needs more details."

    def generate_forecast(self):
        """Generate a sales forecast using the loaded model."""
        if self.model:
            # Example input; you can replace it with dynamic input
            forecast_result = self.model.predict([[2024, 7]])  # Example for July 2024
            return f"Sales forecast for next month: {forecast_result}"
        else:
            return "Sales forecasting model not available."
