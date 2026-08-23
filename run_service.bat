@echo off
rem Headless runner for Task Scheduler (no console, no pause). Output -> logs\svc_app.log
rem Bound to 127.0.0.1 on purpose (local use only; production runs in Docker on the VPS behind Traefik).
cd /d "%~dp0"
if not exist logs mkdir logs
".venv\Scripts\python.exe" -m streamlit run app.py ^
 --server.port 8501 --server.address 127.0.0.1 ^
 --server.headless true --browser.gatherUsageStats false ^
 >> "logs\svc_app.log" 2>&1
