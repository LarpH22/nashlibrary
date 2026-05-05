@echo off
REM MySQL Service Startup Script with Admin Elevation
REM Right-click and select "Run as administrator" if prompted

echo Starting MySQL80 service...
net start MySQL80

if %ERRORLEVEL% equ 0 (
    echo.
    echo SUCCESS: MySQL80 service started successfully!
    echo MySQL is running on port 3306
    echo.
    pause
) else (
    echo.
    echo ERROR: Failed to start MySQL80 service
    echo You may need to run this script with administrator privileges
    echo.
    pause
)
