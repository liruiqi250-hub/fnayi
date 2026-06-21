$ErrorActionPreference = "Stop"

# Try to find Python automatically
$python = if (Get-Command "python" -ErrorAction SilentlyContinue) {
    "python"
} elseif (Get-Command "py" -ErrorAction SilentlyContinue) {
    "py -3"
} else {
    Write-Host "Python not found. Please set the `$python variable manually." -ForegroundColor Red
    exit 1
}

Write-Host "Using Python: $python" -ForegroundColor Cyan

& $python -m PyInstaller `
  --name "BatchFileToolbox" `
  --noconfirm `
  --windowed `
  --paths "src" `
  "src/file_toolbox/main.py"

Write-Host "EXE built at dist\BatchFileToolbox\BatchFileToolbox.exe" -ForegroundColor Green
