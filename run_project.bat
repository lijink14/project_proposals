@echo off
setlocal

echo ==========================================================
echo    Sustainable AI-Ready Cloud Data Center Simulator
echo ==========================================================

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8+ to proceed.
    pause
    exit /b
)

:: 2. Setup Virtual Environment
if not exist "venv" (
    echo Creating Python Virtual Environment...
    python -m venv venv
)

:: 3. Activate Venv
echo Activating Virtual Environment...
call venv\Scripts\activate

:: 4. Install Dependencies
echo Installing Dependencies (this may take a minute)...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b
)

:: 5. Train AI Model (if not exists)
if not exist "models\ppo_datacenter.zip" (
    echo Training AI Model (RL Agent)...
    python training.py
) else (
    echo AI Model found. Skipping training.
)

:: 6. Run Dashboard
echo Starting Simulation Dashboard...
echo Access the dashboard here: http://localhost:8501
streamlit run app.py

pause
