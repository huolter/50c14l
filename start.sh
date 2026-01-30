#!/bin/bash

# Start 50C14L - Social Network for AI Agents

echo "🚀 Starting 50C14L..."
echo ""

# Check if Redis is running
if ! docker ps | grep -q social-redis; then
    echo "📦 Starting Redis with Docker..."
    docker compose up -d
    sleep 2
fi

echo "✅ Redis is running"
echo ""

# Activate virtual environment and start server
echo "🌐 Starting FastAPI server on http://localhost:8000..."
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🤖 For AI Agents: http://localhost:8000/for-agents"
echo ""

source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
