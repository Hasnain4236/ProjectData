@echo off
title Stop All Servers
color 0C

echo.
echo ===============================================================
echo   🛑 Stopping Professional Data Science Platform Servers
echo ===============================================================
echo.

REM Kill all Node.js processes (this will stop both servers)
echo 🔄 Stopping all Node.js processes...
taskkill /f /im node.exe >nul 2>&1

REM Kill any remaining npm processes
taskkill /f /im npm.exe >nul 2>&1

REM Kill any Python processes that might be running
taskkill /f /im python.exe >nul 2>&1

echo ✅ All servers stopped
echo.
echo You can now safely close this window.
pause