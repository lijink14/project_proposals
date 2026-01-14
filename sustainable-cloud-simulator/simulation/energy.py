import numpy as np
import math

class EnergyModel:
    def __init__(self, solar_capacity=100.0, wind_capacity=100.0):
        """
        Simulates renewable energy generation.
        :param solar_capacity: Max theoretical output of solar panels (kW)
        :param wind_capacity: Max theoretical output of wind turbines (kW)
        """
        self.solar_capacity = solar_capacity
        self.wind_capacity = wind_capacity

    def get_solar_power(self, hour: float, cloud_cover: float = 0.0) -> float:
        """
        Generates solar power based on hour of day (0-24).
        Uses a Gaussian distribution peaked at 12:00.
        """
        # Solar window roughly 6am to 6pm
        if hour < 6 or hour > 18:
            return 0.0
        
        # Peak at 12, standard deviation of ~2.5 hours
        mu = 12.0
        sigma = 2.5
        
        # Normal distribution formula un-normalized scalar
        intensity = math.exp(-0.5 * ((hour - mu) / sigma) ** 2)
        
        # Reduce by cloud cover (0.0 to 1.0)
        actual_power = self.solar_capacity * intensity * (1.0 - cloud_cover)
        
        # Add a tiny bit of random noise for realism
        noise = np.random.normal(0, 2)
        return max(0.0, actual_power + noise)

    def get_wind_power(self, hour: float, wind_speed_factor: float = 0.5) -> float:
        """
        Generates wind power. Wind is less predictable than solar.
        modeled as a combination of sine waves to simulate consistency + gusts.
        """
        # Base wind pattern (higher at night often, but variable)
        # Simple curve: sin wave + random
        
        # oscillating factor based on time
        base = math.sin(hour / 4.0) * 0.2 + 0.5 # Oscillates between 0.3 and 0.7 roughly
        
        # Random gust factor
        gust = np.random.normal(0, 0.1)
        
        total_intensity = max(0.0, min(1.0, base + wind_speed_factor + gust))
        
        return self.wind_capacity * total_intensity

    def get_carbon_intensity(self, hour: float) -> float:
        """
        Returns grid carbon intensity in gCO2/kWh.
        Typically high in morning (8-10am) and evening (6-9pm).
        Lower at night or midday (if solar is high in the grid).
        Simulating a "Duck Curve" influenced grid.
        """
        # Base: 400 gCO2/kWh (coal/gas mix)
        base_intensity = 400.0
        
        # Morning Peak (9am)
        morning_peak = 100 * math.exp(-0.5 * ((hour - 9) / 1.5) ** 2)
        
        # Evening Peak (7pm)
        evening_peak = 150 * math.exp(-0.5 * ((hour - 19) / 2.0) ** 2)
        
        return base_intensity + morning_peak + evening_peak
