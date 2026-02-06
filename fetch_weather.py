import requests
import pandas as pd
from datetime import datetime, timedelta

def fetch_historical_weather():
    # Setup dates: Past 6 months
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6*30) 
    
    print(f"Fetching data from {start_date} to {end_date}...")

    # Location: Northern Virginia (Data Center Hub)
    lat = 39.0438
    lon = -77.4874

    # API URL (Open-Meteo Archive)
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ["temperature_2m", "direct_radiation", "wind_speed_10m"],
        "timezone": "auto"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Parse hourly data
        hourly = data['hourly']
        df = pd.DataFrame({
            'time': pd.to_datetime(hourly['time']),
            'temperature_c': hourly['temperature_2m'],
            'solar_radiation_w_m2': hourly['direct_radiation'],
            'wind_speed_kmh': hourly['wind_speed_10m']
        })
        
        # Save to CSV
        output_file = "historical_weather_6mo.csv"
        import os
        abs_path = os.path.abspath(output_file)
        df.to_csv(abs_path, index=False)
        print(f"Successfully saved {len(df)} rows to {abs_path}")
        
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    fetch_historical_weather()
