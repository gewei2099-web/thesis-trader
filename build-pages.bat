@echo off
cd /d %~dp0
if not exist .venv\Scripts\python.exe (
  echo Run setup.ps1 first.
  exit /b 1
)
.\.venv\Scripts\python.exe scripts\build_pages.py
echo.
echo Open docs\index.html locally, or push to GitHub and enable Pages from /docs
