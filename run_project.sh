#!/bin/bash

# Define Directory
PROJECT_DIR="sustainable-cloud-simulator"
cd "$PROJECT_DIR"

echo "=========================================================="
echo "   Sustainable AI-Ready Cloud Data Center Simulator"
echo "=========================================================="

# 1. Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating Python Virtual Environment..."
    python3 -m venv venv
fi

# 2. Activate Venv
source venv/bin/activate

# 3. Install Dependencies
echo "Installing Dependencies..."
pip install -r requirements.txt | grep -v "Requirement already satisfied"

# 4. Train AI Model (if not exists)
if [ ! -f "models/ppo_datacenter.zip" ]; then
    echo "Training AI Model (RL Agent)..."
    python3 training.py
else
    echo "AI Model found. Skipping training."
fi

# 5. Run Dashboard
echo "Starting Simulation Dashboard..."
streamlit run app.py
