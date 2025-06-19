# PowerShell script to build, start FastAPI backend, and open the site in Brave
# 1. Build frontend and backend
# 2. Start FastAPI backend (in a new terminal window)
# 3. Open Brave browser to http://localhost:8080

# Kill any existing uvicorn or python FastAPI processes on port 8080
Write-Host "Killing any existing FastAPI/uvicorn processes on port 8080..."
$port = 8080
$existing = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
if ($existing) {
    $pids = $existing | ForEach-Object { $_.OwningProcess } | Select-Object -Unique
    foreach ($pid in $pids) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Host "Killed process $pid using port $port."
        } catch {
            Write-Host "Could not kill process $pid. It may have already exited."
        }
    }
} else {
    Write-Host "No existing process found on port $port."
}

# Build frontend and backend
Write-Host "Running build_and_copy_frontend.ps1..."
& ./build_and_copy_frontend.ps1

# Start FastAPI backend in a new terminal window
Write-Host "Starting FastAPI backend in a new PowerShell window..."
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080'

# Wait a few seconds for the server to start
Start-Sleep -Seconds 5

# Open Brave browser to the local site (use http://localhost:8080)
Write-Host "Opening Brave browser to http://localhost:8080 ..."
Start-Process "brave.exe" "http://localhost:8080"

Write-Host "Local development environment started."
