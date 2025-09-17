#!/bin/bash

# Professional Data Science Platform - Development Startup Script
# This script starts the development environment with hot reload

echo "🔧 Starting Professional Data Science Platform (Development Mode)..."
echo "====================================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Start development environment
echo "🏗️ Starting development environment..."
docker-compose -f docker-compose.dev.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 20

echo ""
echo "🎉 Development Environment is ready!"
echo "====================================="
echo "📊 Frontend:     http://localhost:3000 (with hot reload)"
echo "🔧 Backend API:  http://localhost:5000 (with nodemon)"
echo "🍃 MongoDB:      mongodb://localhost:27017"
echo "====================================="
echo ""
echo "To view logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "To stop:      docker-compose -f docker-compose.dev.yml down"
echo ""
echo "Happy developing! 🚀"