#!/bin/bash

# Professional Data Science Platform - Production Startup Script
# This script starts the entire application stack with one command

echo "🚀 Starting Professional Data Science Platform..."
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker is running"
echo "✅ Docker Compose is available"

# Pull latest images
echo "📥 Pulling latest base images..."
docker-compose pull

# Build and start services
echo "🏗️ Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check MongoDB
if docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo "✅ MongoDB is healthy"
else
    echo "⚠️ MongoDB is not ready yet"
fi

# Check Backend
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✅ Backend API is healthy"
else
    echo "⚠️ Backend API is not ready yet"
fi

# Check Frontend
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "⚠️ Frontend is not ready yet"
fi

echo ""
echo "🎉 Professional Data Science Platform is starting up!"
echo "=================================================="
echo "📊 Frontend:     http://localhost"
echo "🔧 Backend API:  http://localhost:5000"
echo "❤️ Health Check: http://localhost/health"
echo "=================================================="
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop:      docker-compose down"
echo "To restart:   docker-compose restart"
echo ""
echo "Happy analyzing! 🚀"