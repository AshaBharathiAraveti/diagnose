@echo off
title FreshSense - IoT Food Freshness Monitor
color 0A

:: Use system Python (has TensorFlow + all ML libs)
:: The venv only has sklearn/flask but NOT tensorflow
set SYSPYTHON=C:\Users\hp\AppData\Local\Programs\Python\Python310\python.exe

echo.
echo  ============================================
echo   FreshSense - IoT Food Freshness Monitor
echo  ============================================
echo.
echo  [1] Starting Flask backend server (System Python with TF)...
echo.
cd /d "%~dp0backend"
start "FreshSense Backend" cmd /k "%SYSPYTHON% app.py"
timeout /t 3 /nobreak >nul
echo  [2] Opening dashboard in browser...
start "" "http://localhost:5000"
echo.
echo  [OK] FreshSense is running!
echo       Dashboard: http://localhost:5000
echo       API:       http://localhost:5000/api
echo.
pause
