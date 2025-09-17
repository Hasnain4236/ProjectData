@echo off
REM Professional Data Science Platform - Production Startup Script (Windows)
REM This script starts the entire application stack with one command

echo 🚀 Starting Professional Data Science Platform...
echo ==================================================

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker first.
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo ✅ Docker is running
echo ✅ Docker Compose is available

REM Pull latest images
echo 📥 Pulling latest base images...
docker-compose pull

REM Build and start services
echo 🏗️ Building and starting services...
docker-compose up -d --build

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 30 /nobreak >nul

REM Check service health
echo 🔍 Checking service health...

REM Check Backend
curl -f http://localhost:5000/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend API is healthy
) else (
    echo ⚠️ Backend API is not ready yet
)

REM Check Frontend
curl -f http://localhost/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend is healthy
) else (
    echo ⚠️ Frontend is not ready yet
)

echo.
echo 🎉 Professional Data Science Platform is starting up!
echo ==================================================
echo 📊 Frontend:     http://localhost
echo 🔧 Backend API:  http://localhost:5000
echo ❤️ Health Check: http://localhost/health
echo ==================================================
echo.
echo To view logs: docker-compose logs -f
echo To stop:      docker-compose down
echo To restart:   docker-compose restart
echo.
echo Happy analyzing! 🚀
pause