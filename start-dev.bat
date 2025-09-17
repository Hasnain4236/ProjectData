@echo off
REM Professional Data Science Platform - Development Startup Script (Windows)
REM This script starts the development environment with hot reload

echo 🔧 Starting Professional Data Science Platform (Development Mode)...
echo =====================================================================

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker first.
    pause
    exit /b 1
)

echo ✅ Docker is running

REM Start development environment
echo 🏗️ Starting development environment...
docker-compose -f docker-compose.dev.yml up -d --build

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 20 /nobreak >nul

echo.
echo 🎉 Development Environment is ready!
echo =====================================
echo 📊 Frontend:     http://localhost:3000 (with hot reload)
echo 🔧 Backend API:  http://localhost:5000 (with nodemon)
echo 🍃 MongoDB:      mongodb://localhost:27017
echo =====================================
echo.
echo To view logs: docker-compose -f docker-compose.dev.yml logs -f
echo To stop:      docker-compose -f docker-compose.dev.yml down
echo.
echo Happy developing! 🚀
pause