# Carbon-Aware Cloud Scheduler
**BCA Final Year Project**

## Overview
EcoSync is a **Digital Twin Simulation** of a modern, carbon-aware Cloud Data Center. It uses **Reinforcement Learning (PPO)** to schedule compute tasks around **Solar and Wind energy availability**, minimizing carbon footprint in real time.

Live weather data is pulled directly from the **Open-Meteo Archive API** (Northern Virginia data center region), making every simulation grounded in real-world conditions.

---

## Key Features

- **AI Scheduler** — PPO-trained agent (Stable-Baselines3) decides per hour:
  - `Boost` — Process all queued tasks on clean energy
  - `Eco` — Run only on solar + wind
  - `Defer` — Hold non-critical tasks for a cleaner window

- **Live Weather Data** — Open-Meteo Archive API feeds real solar radiation and wind speed into the simulation (with CSV cache fallback)

- **Solar + Wind Farm** — Independent capacity sliders; both sources factor into AI decisions via combined renewable fraction guardrails

- **Monthly Eco-Audit** — Pick any date and get a full 24h breakdown: stacked bar chart (Grid / Wind / Solar), donut energy mix, AI decision timeline per hour, CO₂ avoided

- **Battery Status Panel** — Real-time charge level with solar/wind input indicators

- **Professional Dashboard** — Soft professional light theme, navy sidebar, emerald accent, all charts with proper contrast

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| AI/ML | Stable-Baselines3 (PPO), Gymnasium |
| Weather Data | Open-Meteo Archive API |
| Charts | Plotly |
| Language | Python 3 |
| Data | Pandas, NumPy |

---

## How to Run

### Mac / Linux
```bash
bash run_project.sh
```

### Windows
```
run_project.bat
```

### Manual
```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Project Structure

```
project_proposals/
├── app.py                        # Main dashboard
├── training.py                   # PPO agent training script
├── fetch_weather.py              # Open-Meteo API utility
├── historical_weather_6mo.csv    # 6-month real weather archive (Northern Virginia)
├── requirements.txt
├── simulation/
│   ├── ai_inference.py           # PPO inference + safety guardrails
│   ├── environment.py            # Gymnasium custom environment
│   ├── energy.py                 # Solar/wind generation models
│   └── workload.py               # Task queue simulation
├── models/
│   └── ppo_datacenter.zip        # Trained AI model
└── assets/
    └── compact.css               # Dashboard theme
```

---

## Data Source

Real weather data sourced from **[Open-Meteo](https://open-meteo.com)** — free, open-source weather API.
Location: Northern Virginia (39.04°N, 77.49°W) — AWS us-east-1 data center region.

---

## Viva Talking Points

1. **AI Decision Logic** — "The PPO agent uses a combined renewable fraction `(solar+wind)/(solar_cap+wind_cap)` so decisions scale correctly regardless of farm size set in the UI."
2. **Live Data** — "The Monthly Eco-Audit fetches real historical weather from Open-Meteo API, cached per date. For future dates it falls back to physics-based simulation seeded by date."
3. **Why PPO?** — "Proximal Policy Optimization handles continuous state spaces well — our state vector includes hour, solar kW, wind kW, carbon intensity, queue depth, and battery level."
