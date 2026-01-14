# Sustainable "AI-Ready" Cloud Data Center Simulator
**BCA Final Year Project**

## 1. Overview
This project is a **Digital Twin Simulation** of a modern, eco-friendly Cloud Data Center. It uses **Artificial Intelligence (Reinforcement Learning)** to optimize computing tasks, ensuring they run when **Renewable Energy** (Solar/Wind) is most available, thereby minimizing the Carbon Footprint.

## 2. Key Features
*   **Environmental Twin**: Simulates realistic 24-hour Solar and Wind energy curves.
*   **AI Agent**: A "Carbon-Aware" scheduler (trained using PPO) that decides whether to:
    *   `PROCESS_ALL`: Clear the queue (High throughput).
    *   `GREEN_ONLY`: Only run tasks powered by Green Energy.
    *   `HOLD`: Delay tasks to wait for better energy (Low Carbon).
*   **Interactive Dashboard**: A Real-time Streamlit UI visualizing the "Energy Mix" and "Carbon Savings".

## 3. Technology Stack
*   **Language**: Python 3
*   **Frontend**: Streamlit
*   **AI/ML**: Stable-Baselines3, Gymnasium (OpenAI)
*   **Data**: Pandas, NumPy

## 4. How to Run
This project includes an automated setup script.

1.  Open your terminal.
2.  Navigate to the project folder.
3.  Run the script:
    ```bash
    bash run_project.sh
    ```
    *This will create a virtual environment, install dependencies, train the AI, and launch the dashboard.*

## 5. Project Structure
*   `app.py`: The Main Dashboard interface.
*   `training.py`: The script that trains the AI agent.
*   `simulation/`: Contains the logic for Energy, Workload, and the Gym Environment.
*   `models/`: Stores the trained AI brain (`ppo_datacenter.zip`).

## 6. How to Present (for Viva)
1.  **Start the App**: Show the dashboard.
2.  **Explain the Graphs**: "See how the Green Line (Solar) goes up at noon? The AI attempts to shift the Red Line (Grid usage) to match it."
3.  **Explain the AI**: "We used Reinforcement Learning. The agent gets 'points' for using Green Energy and loses 'points' for burning coal/grid energy."
