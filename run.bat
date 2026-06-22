@echo off
cd /d %~dp0
if not exist .venv\Scripts\python.exe (
  echo Creating virtual environment...
  py -3.10 -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt
)
echo Starting thesis-trader on http://0.0.0.0:8765
.venv\Scripts\python.exe -m uvicorn src.server:app --host 0.0.0.0 --port 8765 --reload
