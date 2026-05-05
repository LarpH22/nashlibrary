@echo off
setlocal

:: Check for administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo Running as administrator.

set MYSQLD=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe
set MYSQL=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe
set MYSQL_INI=C:\ProgramData\MySQL\MySQL Server 8.0\my.ini
set RESET_SQL=%~dp0reset_password.sql
set RESET_LOG=%TEMP%\mysql-reset.log

echo Stopping MySQL80...
net stop MySQL80 >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: MySQL80 did not stop cleanly or was not running.
)
timeout /t 5 /nobreak >nul

echo Killing stray mysqld processes...
tasklist /FI "IMAGENAME eq mysqld.exe" | findstr /I mysqld.exe >nul
if %errorlevel% equ 0 (
    taskkill /F /IM mysqld.exe >nul 2>&1
)
timeout /t 2 /nobreak >nul

if exist "%RESET_LOG%" del "%RESET_LOG%" >nul 2>&1

echo Starting temporary MySQL server in skip-grant-tables mode...
start "MySQLReset" /B "%MYSQLD%" --defaults-file="%MYSQL_INI%" --skip-grant-tables --console >"%RESET_LOG%" 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Failed to start temporary mysqld process.
    type "%RESET_LOG%"
    pause
    exit /b 1
)
timeout /t 10 /nobreak >nul

echo Resetting root password...
"%MYSQL%" -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'MySQLRoot123!'; FLUSH PRIVILEGES;" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: could not reset root password.
    echo See %RESET_LOG% for details.
    type "%RESET_LOG%"
    goto cleanup
)

echo Stopping temporary MySQL server...
taskkill /F /IM mysqld.exe >nul 2>&1
timeout /t 3 /nobreak >nul

echo Starting MySQL80 service...
net start MySQL80
if %errorlevel% neq 0 (
    echo ERROR: could not start MySQL80 service.
    echo See %RESET_LOG% for details.
    type "%RESET_LOG%"
    pause
    exit /b 1
)

echo Reset complete.
echo Root password is now MySQLRoot123! and .env has been updated.
pause
exit /b 0

:cleanup
echo Cleaning up temporary mysqld...
taskkill /F /IM mysqld.exe >nul 2>&1
echo Reset failed. Please check the log at %RESET_LOG%.
pause
exit /b 1