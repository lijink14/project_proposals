import streamlit as st
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from simulation.environment import DataCenterEnv
from stable_baselines3 import PPO
import os

st.set_page_config(page_title="Sustainable Cloud Simulator", layout="wide")

st.title("🌱 Sustainable 'AI-Ready' Cloud Data Center Simulator")
st.markdown("""
This Digital Twin simulates a data center optimizing its **Carbon Footprint** using Reinforcement Learning.
It balances incoming **Workloads** with available **Solar/Wind Energy**.
""")

# Load Model
@st.cache_resource
def load_model():
    model_path = "models/ppo_datacenter.zip"
    if os.path.exists(model_path):
        return PPO.load(model_path)
    return None

model = load_model()

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Control Panel")
    speed = st.slider("Simulation Speed", 0.1, 2.0, 0.5)
    
    if st.button("Start Simulation"):
        st.session_state.running = True
    
    status_placeholder = st.empty()
    metrics_placeholder = st.container()

with col2:
    st.subheader("Live Analytics (24h Cycle)")
    chart_placeholder = st.empty()
    queue_chart_placeholder = st.empty()

if 'running' in st.session_state and st.session_state.running:
    env = DataCenterEnv()
    obs, _ = env.reset()
    done = False
    
    history_df = pd.DataFrame(columns=['Hour', 'Solar', 'Wind', 'Grid Used', 'Carbon', 'Queue', 'Battery'])
    
    while not done:
        # AI Decision
        if model:
            action, _ = model.predict(obs, deterministic=True)
        else:
            action = env.action_space.sample() # Random if no model
        
        # Step Environment
        obs, reward, done, truncated, info = env.step(action)
        
        # Update Data
        new_row = {
            'Hour': info['hour'], 
            'Solar': info['solar'], 
            'Wind': info['wind'], 
            'Grid Used': info['grid_used'], # Dirty Energy
            'Carbon': info['carbon_emitted'],
            'Queue': info['queue_length'],
            'Battery': info['battery']
        }
        history_df = pd.concat([history_df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Update UI - Status
        status_placeholder.info(f"Hour: {info['hour']}:00 | Queue: {int(info['queue_length'])}")
        
        with metrics_placeholder:
            m1, m2, m3 = st.columns(3)
            m1.metric("Green Energy (kW)", f"{int(info['solar'] + info['wind'])}")
            m2.metric("Grid Energy (kW)", f"{int(info['grid_used'])}", help="Dirty energy pulled from grid")
            m3.metric("Carbon Emitted (g)", f"{int(info['carbon_emitted'])}")
            
            # Action Display
            act_names = ["PROCESS ALL", "GREEN ONLY", "HOLD / WAIT"]
            st.markdown(f"**AI Action:** `{act_names[int(action)]}`")

        # Update UI - Charts
        with chart_placeholder:
            # Combined Energy Plot
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(history_df['Hour'], history_df['Solar'] + history_df['Wind'], label='Renewable (Green)', color='green', alpha=0.7)
            ax.plot(history_df['Hour'], history_df['Grid Used'], label='Grid (Dirty)', color='red', linestyle='--')
            ax.fill_between(history_df['Hour'], history_df['Solar'] + history_df['Wind'], color='green', alpha=0.1)
            ax.set_title("Energy Source Mix")
            ax.set_ylabel("Power (kW)")
            ax.set_xlabel("Hour of Day")
            ax.legend()
            st.pyplot(fig)
            
        with queue_chart_placeholder:
             st.line_chart(history_df.set_index('Hour')[['Queue', 'Battery']])

        time.sleep(speed)
    
    st.success("Simulation Complete for Day 1")
    
    # Final Summary
    total_carbon = history_df['Carbon'].sum()
    st.metric("Total Daily Carbon Footprint", f"{total_carbon:.2f} gCO2")
