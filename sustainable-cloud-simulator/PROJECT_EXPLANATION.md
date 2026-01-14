# Project Explanation: Sustainable "AI-Ready" Cloud Data Center Simulator

## 1. The Core Concept (The "Big Idea")
This project is a **Digital Twin**. Instead of building a real physical data center (which is impossible for a student project), we built a software simulation that **mimics** how a real Google or AWS data center works.

The goal is to solve a specific problem: **Data Centers use too much dirty energy (coal/gas).**
*   **The Solution:** Use Artificial Intelligence to move computing tasks to times when **Solar** and **Wind** energy are peaking.
*   **The Method:** "Temporal Shifting" (Time Shifting). If a task isn't urgent, wait until the sun shines to run it.

---

## 2. How the Project Runs (The Data Flow)
Imagine the simulation as a loop that repeats for every hour of the day (0 to 24).

### Step 1: The Environment (The "World")
We created a virtual world (`simulation/environment.py`) that generates two things every hour:
1.  **Weather Data:** How much Solar/Wind power is available right now? (Based on time of day).
2.  **Workload Data:** How many people are uploading photos or running server tasks right now?

### Step 2: The Agent (The "AI Brain")
This is where the magic happens. The AI looks at the current "State" of the world:
*   *Current Hour:* 2:00 PM
*   *Solar Energy:* High (Sunny) ☀️
*   *Task Queue:* 50 jobs waiting

The AI must choose an **Action**:
*   **Option A (Process All):** Do everything now. (Good for speed, maybe bad for carbon).
*   **Option B (Green Only):** Do only what the solar panels can power.
*   **Option C (Hold):** Wait. (Bad for speed, but maybe saves carbon if it's currently night time).

### Step 3: The Result (Reward System)
After the AI acts, we calculate the result:
*   **Did we use dirty grid energy?** -> Negative Points (Penalty).
*   **Did we clear the queue?** -> Positive Points (Reward).
*   **Did we wait too long?** -> Negative Points (Latency Penalty).

The AI learns from these points over thousands of simulated days during the "Training" phase.

### Step 4: The Visualization (Streamlit)
Finally, we display this on a website (`app.py`). You see a graph with:
*   **Green Line:** Renewable Energy available.
*   **Red Line:** Dirty Grid Energy used.
*   **Goal:** The Red Line should be as low as possible, usually hiding under the Green Line.

---

## 3. Resources & Technology Stack
This project runs entirely in **Python** suitable for a BCA final year submission.

| Component | Technology | Why we used it? |
| :--- | :--- | :--- |
| **Logic & Math** | `NumPy`, `Pandas` | To calculate energy curves and handle data arrays. |
| **Simulation** | `Gymnasium` (OpenAI Gym) | The standard library for building "Games" for AI to learn in. |
| **Artificial Intelligence** | `Stable-Baselines3` | A professional library for Reinforcement Learning (PPO Algorithm). It handles the complex math of the neural network. |
| **Frontend / UI** | `Streamlit` | Creates the beautiful web dashboard with live charts instantly. |
| **Plotting** | `Matplotlib` | Draws the energy curves on the dashboard. |

---

## 4. Deep Dive: How the AI works (Reinforcement Learning)
We are using a technique called **Reinforcement Learning (RL)**.

*   **The Algorithm:** PPO (Proximal Policy Optimization). It's the same family of algorithms used to train ChatGPT's feedback systems.
*   **Training:** When you run `run_project.sh`, the script runs `training.py`.
    *   The AI plays the "Data Center Game" for 10,000 steps.
    *   At first, it guesses randomly. It might run heavy jobs at midnight (creating huge carbon emissions).
    *   It gets a "bad grade" (simulation reward).
    *   It tries again. It learns: *"Ah, at 12:00 PM, there is free Solar energy. If I run tasks then, I get a high score!"*
    *   By the end of training, it has "learned" the pattern of the sun and wind.

---

## 5. Viva Questions & Answers

**Q: Why didn't you use just a simple If-Else statement?**
*   **A:** "If-Else works for simple rules (e.g., 'If Sun > 0, Run'). But real data centers are complex. Maybe the sun is shining, but the battery is full? Maybe it's night, but the battery has charge? Reinforcement Learning figures out the *optimal* balance dynamically, which is better than hard-coded rules."

**Q: What is the 'Carbon Intensity'?**
*   **A:** "It is the measure of how 'dirty' the electricity is. We simulate it being high in the evening (when everyone cooks using grid power) and low during the day (solar)."

**Q: Is this real data?**
*   **A:** "This is a **Synthetic Dataset** generated using Gaussian mathematical curves to simulate realistic patterns. This is standard practice for simulations."
