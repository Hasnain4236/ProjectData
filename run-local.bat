@echo off
title Professional Data Science Platform - Local Development
color 0A

echo.
echo ===============================================================
echo   🚀 Professional Data Science Platform - Local Development
echo ===============================================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js first.
    echo    Download from: https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python first.
    echo    Download from: https://python.org/
    pause
    exit /b 1
)

echo ✅ Node.js and Python are available
echo.

REM Check if npm packages are installed in backend
if not exist "backend\node_modules" (
    echo 📦 Installing backend dependencies...
    cd backend
    npm install
    cd ..
    echo ✅ Backend dependencies installed
) else (
    echo ✅ Backend dependencies already installed
)

REM Check if npm packages are installed in frontend
if not exist "frontend\node_modules" (
    echo 📦 Installing frontend dependencies...
    cd frontend
    npm install --legacy-peer-deps
    cd ..
    echo ✅ Frontend dependencies installed
) else (
    echo ✅ Frontend dependencies already installed
)

echo.
echo 🚀 Starting servers...
echo.

REM Start Backend Server
echo 🔧 Starting Backend Server (Port 5000)...
start "Backend Server" cmd /k "cd backend && npm start"

REM Wait a bit for backend to start
timeout /t 5 /nobreak >nul

REM Start Frontend Server  
echo 🌐 Starting Frontend Server (Port 3000)...
start "Frontend Server" cmd /k "cd frontend && npm start"

echo.
echo 🎉 Professional Data Science Platform is starting!
echo ===============================================================
echo 📊 Frontend:     http://localhost:3000
echo 🔧 Backend API:  http://localhost:5000
echo ❤️ Health Check: http://localhost:5000/api/health
echo ===============================================================
echo.
echo ⭐ Both servers will open in separate windows
echo ⭐ Frontend will automatically open in your browser
echo ⭐ Press Ctrl+C in each window to stop the servers
echo.
echo Happy analyzing! 🚀
echo.
pause