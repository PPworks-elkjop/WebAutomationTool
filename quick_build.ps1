# Quick build script for VERA.exe
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Building VERA.exe" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

Set-Location $PSScriptRoot

Write-Host "Cleaning previous build..." -ForegroundColor Yellow
Remove-Item -Path ".\build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".\VERA.spec" -Force -ErrorAction SilentlyContinue

Write-Host "Starting PyInstaller build...`n" -ForegroundColor Green

python -m PyInstaller `
    --onefile `
    --windowed `
    --name=VERA `
    dashboard_main.py

if (Test-Path ".\dist\VERA.exe") {
    Write-Host "`n================================" -ForegroundColor Green
    Write-Host "SUCCESS! Build complete" -ForegroundColor Green
    Write-Host "================================`n" -ForegroundColor Green
    
    $exe = Get-Item ".\dist\VERA.exe"
    Write-Host "Location: $($exe.FullName)"
    Write-Host "Size: $([math]::Round($exe.Length/1MB,2)) MB"
    Write-Host "Created: $($exe.LastWriteTime)"
} else {
    Write-Host "`nBuild failed. Check output above for errors." -ForegroundColor Red
}
