# Orbit CLI Global Installer
# Purpose: Registers the 'orbit' command globally on this system.

$projectDir = Get-Location
$batchContent = @"
@echo off
cd /d "$projectDir"
python launcher.py %*
"@

$binDir = "$HOME\bin"
if (!(Test-Path $binDir)) {
    New-Item -ItemType Directory -Path $binDir | Out-Null
}

$batchPath = "$binDir\orbit.bat"
$batchContent | Out-File -FilePath $batchPath -Encoding ascii

# Check if binDir is in PATH
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($currentPath -notlike "*$binDir*") {
    $newPath = "$currentPath;$binDir"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    Write-Host "🚀 Orbit added to User PATH." -ForegroundColor Cyan
}

Write-Host "`n✨ Success! The 'orbit' command is now registered." -ForegroundColor Green
Write-Host "👉 Close this terminal and open a new one." -ForegroundColor Yellow
Write-Host "👉 Then just type: orbit" -ForegroundColor Cyan
