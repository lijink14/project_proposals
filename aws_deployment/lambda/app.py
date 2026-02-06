import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "dependency"))
import json
import math
import random
import urllib.request
from datetime import datetime, timedelta

# --- 1. SIMULATED MODEL (Dependency-Free) ---
class EnergyModel:
    def __init__(self, solar_capacity=100.0, wind_capacity=100.0):
        self.solar_capacity = solar_capacity
        self.wind_capacity = wind_capacity

    def get_solar_power(self, hour: float, cloud_cover: float = 0.0) -> float:
        if hour < 6 or hour > 18:
            return 0.0
        
        mu = 12.0
        sigma = 2.5
        intensity = math.exp(-0.5 * ((hour - mu) / sigma) ** 2)
        actual_power = self.solar_capacity * intensity * (1.0 - cloud_cover)
        
        # Random noise (using standard random instead of numpy)
        noise = random.gauss(0, 2)
        return max(0.0, actual_power + noise)

    def get_wind_power(self, hour: float, wind_speed_factor: float = 0.5) -> float:
        base = math.sin(hour / 4.0) * 0.2 + 0.5
        gust = random.gauss(0, 0.1)
        total_intensity = max(0.0, min(1.0, base + wind_speed_factor + gust))
        return self.wind_capacity * total_intensity

    def get_carbon_intensity(self, hour: float) -> float:
        base_intensity = 400.0
        morning_peak = 100 * math.exp(-0.5 * ((hour - 9) / 1.5) ** 2)
        evening_peak = 150 * math.exp(-0.5 * ((hour - 19) / 2.0) ** 2)
        return base_intensity + morning_peak + evening_peak

# --- 2. REAL MODEL (Open-Meteo) ---
def fetch_real_weather(lat=39.0438, lon=-77.4874):
    # Fetch today's forecast/history
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&hourly=temperature_2m,direct_radiation,wind_speed_10m&timezone=auto"
    
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return data
            else:
                return {"error": f"API returned status {response.status}"}
    except Exception as e:
        return {"error": str(e)}

# --- 3. LAMBDA HANDLER ---
def lambda_handler(event, context):
    """
    Query Params (GET) OR JSON Body (POST):
    - mode: 'simulated' (default) or 'real'
    - hour: 0-23
    - solar, wind, carbon, queue, battery (for allocation)
    """
    # 1. Parse Input (Support both Query Params and JSON Body)
    params = {}
    
    # Check for Query Params
    if event.get('queryStringParameters'):
        params.update(event.get('queryStringParameters'))
        
    # Check for JSON Body
    if event.get('body'):
        try:
            body_data = json.loads(event.get('body'))
            if isinstance(body_data, dict):
                params.update(body_data)
        except:
            pass
            
    mode = params.get('mode', 'simulated')
    
    response_body = {}
    
    if mode == 'real':
        lat = params.get('lat', 39.0438)
        lon = params.get('lon', -77.4874)
        data = fetch_real_weather(lat, lon)
        response_body = {
            "source": "Open-Meteo API",
            "data": data
        }
    elif mode == 'allocate':
        # Resource Allocation Mode (AI Inference Logic)
        try:
            # Parse param inputs
            solar = float(params.get('solar', 0))
            wind = float(params.get('wind', 0)) # Not used in simple rules yet but good to have
            carbon = float(params.get('carbon', 200))
            queue = float(params.get('queue', 10))
            battery = float(params.get('battery', 50))
            
            # --- LOGIC PORTED FROM LOCAL SIMULATION ---
            # Default action: 0 (Process All)
            action = 0 
            
            # --- PPO MODEL INFERENCE (ONNX) ---
            # Try to load ONNX model (assuming it's bundled in models/ppo_datacenter.onnx)
            # --- PPO MODEL INFERENCE (ONNX) ---
            # Patch for numpy on Windows-developed zip deployed to Linux Lambda
            if os.name == 'posix' and not hasattr(os, 'add_dll_directory'):
                 # Create dummy function to prevent numpy from crashing on import
                 def dummy_add_dll_directory(path):
                     pass
                 os.add_dll_directory = dummy_add_dll_directory

            import numpy as np
            try:
                import onnxruntime as ort
                model_path = os.path.join(os.path.dirname(__file__), "models", "ppo_datacenter.onnx")
                
                if os.path.exists(model_path):
                    session = ort.InferenceSession(model_path)
                    
                    # Observation: [Hour, Solar, Wind, Carbon, Queue, Battery, 0]
                    # We need 'hour' param which we didn't parse above, adding default
                    hour = float(params.get('hour', 12.0))
                    
                    obs = np.array([[hour, solar, wind, carbon, queue, battery, 0]], dtype=np.float32)
                    input_name = session.get_inputs()[0].name
                    
                    # Run inference
                    actions = session.run(None, {input_name: obs})[0]
                    action = int(actions[0])
            except Exception as e:
                # Fallback if ONNX runtime not available or model missing
                # print(f"Model inference failed: {e}")
                pass

            # 2. Safety Guardrails (Deterministic Rules)
            # These override the model for safety/efficiency
            if carbon > 500 and solar < 50:
                action = 2 # HOLD (Dirty grid, no sun)
            elif queue > 450 and (solar > 20 or battery > 40):
                action = 0 # BOOST (Backlog critical)
            elif solar > 350:
                action = 0 # BOOST (Free energy)
            
            # 3. Decision Mapping
            action_map = {
                0: "🚀 Boost (Process All)",
                1: "🌱 Eco (Green Only)",
                2: "🛑 Defer (Hold Load)"
            }
            
            response_body = {
                "source": "Cloud AI Allocator",
                "action_id": action,
                "action_label": action_map.get(action, "Unknown"),
                "reasoning": f"Carbon: {carbon}, Solar: {solar}"
            }
            
        except Exception as e:
            response_body = {"error": f"Allocation failed: {str(e)}"}

    else:
        # Simulated Mode
        try:
            hour = float(params.get('hour', 12.0))
        except ValueError:
            hour = 12.0
            
        model = EnergyModel()
        solar = model.get_solar_power(hour)
        wind = model.get_wind_power(hour)
        carbon = model.get_carbon_intensity(hour)
        
        response_body = {
            "source": "Internal Simulation Model",
            "params": {"hour": hour},
            "prediction": {
                "solar_power_kw": round(solar, 2),
                "wind_power_kw": round(wind, 2),
                "carbon_intensity_g_kwh": round(carbon, 2)
            }
        }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(response_body)
    }
