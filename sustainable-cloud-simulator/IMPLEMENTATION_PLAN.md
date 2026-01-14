# Sustainable "AI-Ready" Cloud Data Center Simulator - Implementation Plan

## 1. Project Analysis
This project aims to build a **Carbon-Aware Cloud Scheduler** that optimizes when computing tasks are executed to minimize carbon footprint. It bridges the gap between **Cloud Computing**, **Data Science** (Renewable Energy Prediction), and **Reinforcement Learning** (smart scheduling).

### Core Problem
Data centers often run non-urgent workloads during peak grid demand (high carbon intensity).
### Solution
A "Digital Twin" simulator that:
1.  Predicts renewable energy availability (Solar/Wind).
2.  Uses an RL Agent (AI) to decide whether to **Execute**, **Delay**, or **Hibernate** tasks.
3.  Visualizes the impact (Carbon Avoided) via a dashboard.

## 2. Architecture Design
We will build a **Local Simulation** that mimics the AWS architecture acting as a "Digital Twin". This ensures the project is portable, free to run, and easy to demonstrate for your BCA evaluation.

### Components
1.  **Environmental Twin (Data Layer):**
    *   Generates/Simulates 24-hour Solar & Wind curves.
    *   Simulates Grid Carbon Intensity (heavy usage = dirty power).
    *   Simulates incoming Task Queue (bursts of computing jobs).
2.  **Smart Agent (AI Layer):**
    *   **Algorithm:** Deep Q-Network (DQN) or PPO (Proximal Policy Optimization).
    *   **Input (State):** Current Time, Battery/Green Energy Level, Queue Length.
    *   **Output (Action):** Run Task, Delay Task (Store in Queue).
    *   **Reward:** +Points for using Solar, -Points for Grid usage or dropping tasks.
3.  **Dashboard (Presentation Layer):**
    *   **Tool:** Streamlit.
    *   **Features:** Live animation of the 24h cycle, graphs of Green vs. Brown energy used, queue status.

## 3. Technology Stack (Simulated)
*   **Language:** Python 3.9+
*   **Frontend:** Streamlit (for the Dashboard/UI)
*   **AI/RL:** Stable-Baselines3, Gymnasium (OpenAI Gym)
*   **Data:** Pandas, NumPy, Matplotlib/Plotly

## 4. Development Roadmap

### Phase 1: Foundation & Data Simulation (Day 1)
*   Set up Python environment.
*   `energy_model.py`: Create functions to generate synthetic Solar/Wind curves based on time of day.
*   `workload_model.py`: Create a function to simulate incoming server traffic.

### Phase 2: The RL Environment (Day 1-2)
*   `datacenter_env.py`: Create a custom Gym Environment (`DataCenterEnv`).
    *   `step()` function: Updates the time, energy, and queue.
    *   `reset()` function: Starts a new day.

### Phase 3: AI Implementation (Day 2)
*   `train_agent.py`: Use Stable-Baselines3 to train onto the `DataCenterEnv`.
*   Save the trained model.

### Phase 4: Dashboard & Integration (Day 3)
*   `app.py`: Build the Streamlit interface.
*   Integrate the trained model to make decisions in real-time on the dashboard.
*   Plot "Carbon Footprint Saved" metrics.

## 5. Directory Structure
```
sustainable-cloud-simulator/
├── app.py                 # Main Streamlit Dashboard
├── training.py            # Script to train the AI
├── models/                # Saved RL models
├── simulation/
│   ├── energy.py          # Solar/Wind logic
│   ├── workload.py        # Task queue logic
│   └── environment.py     # Gym Environment
└── requirements.txt       # Dependencies
```
