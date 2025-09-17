@echo off
echo 🚀 Quick Start - Professional Data Science Platform
echo.

REM Start Backend
start "Backend" cmd /k "cd backend && npm start"

REM Start Frontend  
start "Frontend" cmd /k "cd frontend && npm start"

echo ✅ Servers starting in separate windows
echo 📊 Frontend: http://localhost:3000
echo 🔧 Backend:  http://localhost:5000
pause