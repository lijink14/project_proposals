import numpy as np
import pandas as pd

def get_service_metrics(total_power, queue_length):
    """
    Breaks down the total power usage into different hypothetical services.
    Returns a dictionary of metrics.
    """
    # Synthetic distribution of load
    breakdown = {
        "AI Training Models": 0.45,  # High compute
        "Cloud Storage (S3)": 0.20,  # Medium
        "Database Queries": 0.15,
        "Web Hosting": 0.10,
        "Network Traffic": 0.10
    }
    
    metrics = []
    for service, ratio in breakdown.items():
        metrics.append({
            "Service": service,
            "Power Usage (kW)": total_power * ratio,
            "Active Threads": int(queue_length * ratio * 10) + np.random.randint(5, 50),
            "Carbon Footprint (g)": float(total_power * ratio * 0.4) # Approx coefficient
        })
    
    return pd.DataFrame(metrics)

def get_yearly_projections(current_daily_carbon, baseline_daily_carbon):
    """
    Generates a 12-month projection comparing AI-Cloud vs Traditional Cloud.
    """
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Simulate seasonal variations (Solar better in summer)
    base_savings = max(0, baseline_daily_carbon - current_daily_carbon)
    
    data = []
    accumulated_savings = 0
    
    for i, month in enumerate(months):
        # Seasonal factor: Summer (Jun-Aug) has better renewable yield -> higher savings
        seasonatility = 1.0 + (0.3 * np.sin(i / 12 * np.pi)) 
        
        monthly_ai_carbon = current_daily_carbon * 30 * (1/seasonatility)
        monthly_trad_carbon = baseline_daily_carbon * 30 
        
        savings = monthly_trad_carbon - monthly_ai_carbon
        accumulated_savings += savings
        
        data.append({
            "Month": month,
            "Traditional Cloud (kgCO2)": monthly_trad_carbon / 1000,
            "EcoSync AI Cloud (kgCO2)": monthly_ai_carbon / 1000,
            "Net Savings (kgCO2)": savings / 1000
        })
        
    return pd.DataFrame(data)

def get_cost_analysis(green_energy_kw, grid_energy_kw):
    """
    Calculates cost based on hypothetical tariffs.
    Grid Energy: €0.30 / kWh
    Solar/Wind: €0.05 / kWh (Maintenance cost)
    """
    cost_grid = grid_energy_kw * 0.30
    cost_green = green_energy_kw * 0.05
    
    total_cost = cost_grid + cost_green
    # Traditional cost (assuming all was grid)
    trad_cost = (green_energy_kw + grid_energy_kw) * 0.30
    
    return total_cost, trad_cost

def get_live_users(hour):
    """
    Simulates user activity curve based on time of day.
    Peak at 14:00 and 20:00.
    """
    # Simple double gaussian shape
    base_users = 1200
    activity = 800 * (np.exp(-((hour - 14)**2)/10) + np.exp(-((hour - 20)**2)/10))
    noise = np.random.randint(-50, 50)
    return int(base_users + activity + noise)
