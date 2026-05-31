param(
    [switch]$WithIcon
)

$ErrorActionPreference = "Stop"

Write-Host "Building BlenderTutor executable..."

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    throw "Virtual environment not found. Create it first with: python -m venv venv"
}

& .\venv\Scripts\python.exe -m pip install -r requirements.txt
& .\venv\Scripts\python.exe -m pip install pyinstaller

$pyiArgs = @(
    "--noconfirm"
    "--clean"
    "--name", "BlenderTutor"
    "--windowed"
    "--onefile"
)

if ($WithIcon) {
    if (-not (Test-Path ".\assets\watchfulai.ico")) {
        throw "Icon requested but not found at .\assets\watchfulai.ico"
    }
    $pyiArgs += @("--icon", ".\assets\watchfulai.ico")
}

$pyiArgs += "main.py"

& .\venv\Scripts\pyinstaller.exe @pyiArgs

Write-Host ""
Write-Host "Build complete:"
Write-Host "  .\dist\BlenderTutor.exe"
Write-Host ""
Write-Host "Run with:"
Write-Host "  .\dist\BlenderTutor.exe"
