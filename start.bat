@echo off
cd /d "C:\Users\krist\Claude Trading Test\scb statistics"
C:\Python313\python.exe -m streamlit run "scb_salaries.py" --server.port 8502
pause
