import gymnasium as gym
from gymnasium import spaces
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

    def infer_action(self, hour, solar, wind, carbon, queue, battery):
        """
        Runs the logic through the actual Trained PPO Model with Safety Guardrails.
        Observation: [Hour, Solar, Wind, Carbon, Queue, Battery, 0]
        """
        # 1. AI Model Prediction
        action = 0 
        if self.model:
            obs = np.array([hour, solar, wind, carbon, queue, battery, 0], dtype=np.float32)
            try:
                action, _ = self.model.predict(obs, deterministic=True)
                action = int(action)
            except:
                action = 0
        
        # 2. Safety Guardrails
        if carbon > 500 and solar < 50:
            action = 2 
        elif queue > 450 and (solar > 20 or battery > 40):
            action = 0 
        elif solar > 350:
            action = 0

        action_map = {
            0: "🚀 Boost (Process All)",
            1: "🌱 Eco (Green Only)",
            2: "🛑 Defer (Hold Load)"
        }
        
        return action_map.get(action, "Unknown"), action
        
        if action == 0: # PROCESS_ALL
            # Try to clear queue
            possible_tasks = int(self.queue)
            energy_needed = possible_tasks * energy_per_task
            
            tasks_processed = possible_tasks
            power_consumed = energy_needed
            
        elif action == 1: # PROCESS_GREEN
            # Calculate max tasks we can run with green energy
            possible_by_energy = int(green_energy_available / energy_per_task)
            possible_tasks = min(self.queue, possible_by_energy)
            
            tasks_processed = possible_tasks
            power_consumed = possible_tasks * energy_per_task
            
        elif action == 2: # HOLD
            tasks_processed = 0
            power_consumed = 0.5 # Base load power (idle servers)
        
        # 3. Calculate Energy Mix (Green vs Grid)
        # First use Green, then Grid
        green_used = min(green_energy_available, power_consumed)
        grid_used = max(0, power_consumed - green_energy_available)
        
        # Update Battery (Simple logic: if surplus green, charge it; if used green, drain it)
        # Note: In PROCESS_ALL, we might use battery then grid.
        # In PROCESS_GREEN, we shouldn't touch grid ideally, but we count battery as green.
        
        if power_consumed < (solar + wind):
            # Surplus -> Charge Battery
            surplus = (solar + wind) - power_consumed
            self.battery = min(self.battery_capacity, self.battery + surplus)
        else:
            # Deficit -> Drain Battery first
            # We already accounted for this in green_used logic roughly, but let's update state
            needed_from_storage = power_consumed - (solar + wind)
            actual_drain = min(self.battery, max(0, needed_from_storage))
            self.battery -= actual_drain
            
            # Recalculate grid used more precisely
            total_green_supply = (solar + wind) + actual_drain
            grid_used = max(0, power_consumed - total_green_supply)
            green_used = total_green_supply # This is effectively what we used

        # Update Queue
        self.queue -= tasks_processed
        
        # 4. Calculate Reward
        # Minimize Carbon, Maximize Throughput, Minimize Drop/Latency
        
        carbon_footprint = grid_used * carbon_intensity # gCO2
        
        reward = 0
        reward += (tasks_processed * 1.0) # Good to do work
        reward -= (carbon_footprint * 0.05) # Bad to emit carbon
        reward -= (dropped_tasks * 2.0) # Very bad to drop tasks
        reward -= (self.queue * 0.1) # Penalty for longer queue (latency)
        
        # 5. Move Time
        self.current_hour += 1
        done = False
        if self.current_hour >= 24:
            # End of Episode (Day)
            done = True
        
        # Info for dashboard
        info = {
            "hour": self.current_hour - 1,
            "solar": solar,
            "wind": wind,
            "grid_used": grid_used,
            "carbon_emitted": carbon_footprint,
            "tasks_processed": tasks_processed,
            "queue_length": self.queue,
            "battery": self.battery
        }
        self.history.append(info)
        
        return self._get_obs(), reward, done, False, info
