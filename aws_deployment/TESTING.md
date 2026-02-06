# Testing Your Weather API

**🚀 Live API Endpoint:**
`https://5nx0a507lb.execute-api.ap-south-1.amazonaws.com/prod/weather`

You can test it using a Browser, Curl, or Postman.

## 1. Resource Allocation Mode (The AI Decision)
**Use this to get the cloud-based AI decision on how to handle workloads.**

**URL Example:**
```
/weather?mode=allocate&solar=400&carbon=150&queue=50&battery=80
```

**Parameters:**
- `mode=allocate`: Trigger the allocation logic.
- `solar`: Current solar generation (kW).
- `carbon`: Grid carbon intensity (g/kWh).
- `queue`: Current task queue length.
- `battery`: Battery charge level (%).

**Response:**
```json
{
  "source": "Cloud AI Allocator",
  "action_id": 0,
  "action_label": "🚀 Boost (Process All)",
  "reasoning": "Carbon: 150.0, Solar: 400.0"
}
```

---

## 2. Real Weather Mode (Open-Meteo Proxy)
**Use this to fetch live/historical weather data for a specific location.**

**URL Example:**
```
/weather?mode=real&lat=39.04&lon=-77.48
```

**Parameters:**
- `mode=real`: Trigger the Open-Meteo fetcher.
- `lat`, `lon`: Latitude and Longitude (default: Northern Virginia).

**Response:**
```json
{
  "source": "Open-Meteo API",
  "data": { ... }
}
```

---

## 3. Simulated Prediction Mode (Internal Model)
**Use this to get a predicted solar/wind value for a specific hour using the internal math model.**

**URL Example:**
```
/weather?mode=simulated&hour=14
```

**Parameters:**
- `mode=simulated` (default).
- `hour`: Hour of the day (0-23).

**Response:**
```json
{
  "source": "Internal Simulation Model",
  "prediction": {
    "solar_power_kw": 85.4,
    "wind_power_kw": 32.1,
    "carbon_intensity_g_kwh": 410.5
  }
}
```

## How to Deploy & Get URL
Run the following in your terminal (if you have AWS SAM CLI):
```bash
cd aws_deployment
sam deploy --guided
```
Look for `WeatherApiEndpoint` in the output!
