import numpy as np
import math

class WorkloadGenerator:
    def __init__(self, max_tasks_per_hour=100):
        self.max_tasks = max_tasks_per_hour
    
    def get_incoming_tasks(self, hour: float) -> int:
        """
        Simulates number of new task requests arriving at the data center.
        Pattern: Business hours (9-5) are busy.
        """
        # Base traffic
        if 8 <= hour <= 18:
            # Business hours: High traffic
            base = 0.7
        else:
            # Off hours: Low traffic
            base = 0.2
            
        # Add variability
        variability = np.random.uniform(-0.1, 0.2)
        
        # Occasional burst (5% chance)
        burst = 0.5 if np.random.random() < 0.05 else 0.0
        
        intensity = max(0.0, min(1.0, base + variability + burst))
        
        return int(self.max_tasks * intensity)

    def get_task_complexity(self) -> float:
        """
        Returns a multiplier for how hard the tasks are (power consumption factor).
        Normal distribution around 1.0
        """
        return max(0.1, np.random.normal(1.0, 0.2))
