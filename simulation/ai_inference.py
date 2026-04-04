import numpy as np
from stable_baselines3 import PPO
import os

class AIInferenceEngine:
    def __init__(self, model_path="models/ppo_datacenter.zip"):
        self.model = None
        if os.path.exists(model_path):
            try:
                self.model = PPO.load(model_path)
            except Exception as e:
                pass

    def infer_action(self, hour, solar, wind, carbon, queue, battery,
                     solar_capacity=850, wind_capacity=200):
        """
        Runs inference through the trained PPO model with calibrated safety guardrails.

        Guardrails use combined renewable fraction (solar + wind) / (solar_cap + wind_cap)
        so they scale correctly regardless of farm sizes set in the UI.

        Args:
            hour          : current hour of day (0-23)
            solar         : current solar generation (kW)
            wind          : current wind generation (kW)
            carbon        : grid carbon intensity (gCO2/kWh)
            queue         : pending task count
            battery       : battery charge level (kWh or %)
            solar_capacity: rated solar farm capacity (kW)
            wind_capacity : rated wind farm capacity (kW)
        """
        energy_per_task = 0.1  # kWh per task (matches environment.py)

        # --- 1. PPO Model Prediction ---
        action = 0
        if self.model:
            obs = np.array([hour, solar, wind, carbon, queue, battery, 0], dtype=np.float32)
            try:
                action, _ = self.model.predict(obs, deterministic=True)
                action = int(action)
            except Exception:
                action = 0

        # --- 2. Calibrated Safety Guardrails ---
        # Use combined renewable fraction so wind supplements solar in decisions.

        total_capacity = max(1.0, solar_capacity + wind_capacity)
        combined_renewable = solar + wind
        combined_fraction = combined_renewable / total_capacity   # 0.0 – 1.0

        # Total green supply (renewables + battery storage)
        green_available = combined_renewable + battery

        # kWh needed to clear the current task queue
        estimated_demand = max(1.0, queue * energy_per_task)

        # Can green supply cover current demand? >= 1.0 means fully covered
        green_coverage = green_available / estimated_demand

        # Rule 1 — Dirty grid + very low combined renewables → defer non-urgent work
        if carbon > 500 and combined_fraction < 0.15:
            action = 2  # HOLD

        # Rule 2 — Critical backlog + meaningful renewables available + green covers half → clear it
        elif queue > 400 and combined_fraction > 0.15 and green_coverage >= 0.5:
            action = 0  # PROCESS_ALL

        # Rule 3 — Combined renewables above 55 % of total capacity → abundant clean energy, boost
        elif combined_fraction > 0.55:
            action = 0  # PROCESS_ALL

        # Rule 4 — Moderate combined renewables (25-55 %) + reasonably clean grid → prefer eco mode
        # Only overrides HOLD; keeps PROCESS_ALL if the model chose it
        elif combined_fraction > 0.25 and carbon < 450:
            if action == 2:
                action = 1  # ECO (Green Only)

        action_map = {
            0: "🚀 Boost (Process All)",
            1: "🌱 Eco (Green Only)",
            2: "🛑 Defer (Hold Load)"
        }

        return action_map.get(action, "Unknown"), action
