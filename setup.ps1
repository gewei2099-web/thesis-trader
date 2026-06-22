Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    py -3.10 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
}

Write-Host "Setup complete. Run: .\run.bat or:"
Write-Host "  .\.venv\Scripts\python.exe -m uvicorn src.server:app --host 0.0.0.0 --port 8765 --reload"
