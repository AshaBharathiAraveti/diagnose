@echo off
echo ===================================================
echo  FreshSense - Opening Port 5000 for ESP32
echo ===================================================
echo.

netsh advfirewall firewall delete rule name="FreshSense Flask Port 5000" >nul 2>&1
netsh advfirewall firewall add rule name="FreshSense Flask Port 5000" dir=in action=allow protocol=TCP localport=5000

if %errorlevel%==0 (
    echo.
    echo  SUCCESS! Port 5000 is now open.
    echo  Your ESP32 can now reach the Flask server.
    echo.
) else (
    echo.
    echo  FAILED - Please make sure you right-clicked
    echo  this file and chose "Run as administrator"
    echo.
)

pause
