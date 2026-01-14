import gymnasium as gym
from gymnasium import spaces
import numpy as np
from .energy import EnergyModel
from .workload import WorkloadGenerator

class DataCenterEnv(gym.Env):
    """
    Custom Environment that follows gym interface.
    Represents a Cloud Data Center trying to optimize for Carbon usage.
    """
    metadata = {'render.modes': ['human']}

    def __init__(self):
        super(DataCenterEnv, self).__init__()
        
        # Simulation Parameters
        self.energy_model = EnergyModel()
        self.workload_model = WorkloadGenerator()
        self.max_queue_size = 500
        self.battery_capacity = 200.0 # kWh
        
        # State:
        # 0: Hour of Day (0-24)
        # 1: Solar Gen (kW)
        # 2: Wind Gen (kW)
        # 3: Grid Carbon Intensity (g/kWh)
        # 4: Current Queue Length (num tasks)
        # 5: Battery Level (kWh)
        # 6: Average Task Age (simulated latency)
        
        low = np.array([0, 0, 0, 0, 0, 0, 0])
        high = np.array([24, 500, 500, 1000, self.max_queue_size, self.battery_capacity, 100])
        
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

        # Actions:
        # 0: PROCESS_ALL (Run as many tasks as possible, use Grid if needed)
        # 1: PROCESS_GREEN (Run tasks only up to available Green Energy, queue rest)
        # 2: HOLD (Defer all tasks to next hour)
        self.action_space = spaces.Discrete(3)

        # Init state
        self.current_hour = 0
        self.queue = 0
        self.battery = self.battery_capacity * 0.5 # Start 50% charged
        self.day_count = 0
        
        # Metrics for dashboard
        self.history = []

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_hour = 0
        self.queue = 0
        self.battery = self.battery_capacity * 0.5
        self.day_count = 0
        self.history = []
        return self._get_obs(), {}

    def _get_obs(self):
        solar = self.energy_model.get_solar_power(self.current_hour)
        wind = self.energy_model.get_wind_power(self.current_hour)
        carbon = self.energy_model.get_carbon_intensity(self.current_hour)
        
        return np.array([
            self.current_hour,
            solar,
            wind,
            carbon,
            self.queue,
            self.battery,
            0 # Task age placeholder
        ], dtype=np.float32)

    def step(self, action):
        # 1. Update Environment State (New Tasks / Weather)
        
        current_obs = self._get_obs()
        solar = current_obs[1]
        wind = current_obs[2]
        carbon_intensity = current_obs[3]
        
        incoming_tasks = self.workload_model.get_incoming_tasks(self.current_hour)
        self.queue += incoming_tasks
        
        # Cap queue (simulation of dropped packets)
        dropped_tasks = max(0, self.queue - self.max_queue_size)
        self.queue = min(self.queue, self.max_queue_size)
        
        # 2. Execute Action
        tasks_processed = 0
        power_consumed = 0.0 # kWh
        
        # Energy available from renewables
        green_energy_available = solar + wind + self.battery
        
        # Task energy cost constant (e.g., 0.5 kWh per 10 tasks)
        energy_per_task = 0.1 
        
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
