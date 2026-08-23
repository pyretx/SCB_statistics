@echo off
rem SCB Statistics launcher. The app normally runs hidden as scheduled task "SCBStatistics" (install_task.ps1).
rem If it is already listening on 8501 -> just open the browser; else start the task (or, without the task, run it here).
cd /d "%~dp0"
netstat -ano | findstr ":8501 " | findstr LISTENING >nul 2>&1
if %errorlevel%==0 goto open
schtasks /query /tn SCBStatistics >nul 2>&1
if %errorlevel%==0 (
  echo Starting SCBStatistics service task...
  schtasks /run /tn SCBStatistics >nul 2>&1
  timeout /t 6 /nobreak >nul
) else (
  echo No service task installed - starting in this window (run install_task.ps1 to install the service)...
  start "SCB Statistics (8501)" /min cmd /c "".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true"
  timeout /t 6 /nobreak >nul
)
:open
start "" http://localhost:8501
