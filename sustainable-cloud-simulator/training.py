import gymnasium as gym
from stable_baselines3 import PPO, DQN
from simulation.environment import DataCenterEnv
import os
import numpy as np

def train():
    # Create logs directory
    log_dir = "tmp/"
    os.makedirs(log_dir, exist_ok=True)

    # Initialize Environment
    env = DataCenterEnv()
    
    # Initialize Agent
    # We use PPO (Proximal Policy Optimization) - good generic RL algorithm
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=log_dir)
    
    print("Training Agent for 10,000 steps...")
    model.learn(total_timesteps=10000)
    
    # Save Model
    save_path = "models/ppo_datacenter"
    model.save(save_path)
    print(f"Model saved to {save_path}")
    
    return model

def test(model=None):
    env = DataCenterEnv()
    
    if model is None:
        model_path = "models/ppo_datacenter"
        if os.path.exists(model_path + ".zip"):
            model = PPO.load(model_path)
        else:
            print("No model found. Running Random Agent.")
            model = None

    obs, _ = env.reset()
    done = False
    
    print("\n--- Testing Trained Agent (One Day Simulation) ---")
    print(f"{'Hour':<5} | {'Action':<15} | {'Solar':<8} | {'TaskQ':<6} | {'Grid(kWh)':<10} | {'Carbon(g)':<10}")
    
    total_carbon = 0
    total_tasks = 0
    
    while not done:
        if model:
            action, _ = model.predict(obs, deterministic=True)
        else:
            action = env.action_space.sample()
            
        obs, reward, done, truncated, info = env.step(action)
        
        # Decode action for print
        act_str = ["PROCESS_ALL", "GREEN_ONLY", "HOLD"][int(action)]
        
        print(f"{info['hour']:<5} | {act_str:<15} | {info['solar']:.1f}    | {info['queue_length']:<6} | {info['grid_used']:.2f}      | {info['carbon_emitted']:.1f}")
        
        total_carbon += info['carbon_emitted']
        total_tasks += info['tasks_processed']
        
    print("-" * 70)
    print(f"Total Carbon Emitted: {total_carbon:.2f} g")
    print(f"Total Tasks Processed: {total_tasks}")

if __name__ == "__main__":
    trained_model = train()
    test(trained_model)
