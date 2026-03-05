@echo off
title Deal Flow Engine - Launcher
echo =======================================================
echo       STARTING DEAL FLOW ENGINE (AUTOPILOT + UI)
echo =======================================================
echo.

:: Ensure we are in the exact directory where the batch script lives
cd /d "%~dp0"

:: Force UTF-8 encoding so emojis print properly in the console
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

:: Step 1: Open a new terminal window and run the background autopilot schedule
echo [1] Starting Python AI Auto-Pilot Engine...
start "Deal Flow Data Miner & Mailer" cmd /k "python run.py --schedule"

:: Give it 2 seconds to boot before launching the dashboard
timeout /t 2 /nobreak > nul

:: Step 2: Open a new terminal window and launch the Streamlit frontend
echo [2] Starting Streamlit Real-Time Dashboard...
start "Deal Flow Dashboard UI" cmd /k "streamlit run dashboard.py"

echo.
echo =======================================================
echo  SUCCESS!
echo  The Engine is now running. Keep the two new windows
echo  open in the background!
echo =======================================================
pause
