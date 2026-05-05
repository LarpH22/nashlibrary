# Start MySQL Service with Admin Elevation
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Requesting administrator privileges..."
    $arguments = "-NoExit -NoProfile -File `"$PSCommandPath`""
    Start-Process -FilePath powershell -ArgumentList $arguments -Verb RunAs
    exit
}

Write-Host "Starting MySQL80 service..." -ForegroundColor Green
Start-Service -Name "MySQL80"
Write-Host "MySQL80 service started successfully!" -ForegroundColor Green
Get-Service -Name "MySQL80" | Select-Object -Property Name, Status
