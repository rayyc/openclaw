#!/bin/bash
# OpenClaw Complete System Starter/Stopper
# Usage: ./run_system.sh start
#        ./run_system.sh stop
#        ./run_system.sh

ACTION="${1:-start}"

function start_openclaw() {
    echo "🚀 Starting OpenClaw System..."
    echo ""
    
    # Start Docker Compose
    echo "📦 Starting Docker containers (PostgreSQL, Redis)..."
    docker-compose up -d
    sleep 3
    
    # Start backend in a new terminal window
    echo "⚙️  Starting Backend (Uvicorn on http://127.0.0.1:8000/docs)..."
    source .venv/bin/activate
    uvicorn backend.main:app --reload &
    BACKEND_PID=$!
    
    sleep 5
    
    # Start frontend
    echo "🎨 Starting Frontend (Next.js on http://localhost:3000)..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    
    sleep 3
    
    echo ""
    echo "✅ System Started!"
    echo ""
    echo "Frontend:  http://localhost:3000"
    echo "Backend API Docs:  http://127.0.0.1:8000/docs"
    echo "PostgreSQL: localhost:5432"
    echo "Redis: localhost:6379"
    echo ""
    echo "📝 To stop the system, run: ./run_system.sh stop"
    echo ""
    
    # Save PIDs
    echo "$BACKEND_PID $FRONTEND_PID" > .openclaw_pids.txt
}

function stop_openclaw() {
    echo "🛑 Stopping OpenClaw System..."
    echo ""
    
    # Stop processes
    if [ -f ".openclaw_pids.txt" ]; then
        read BACKEND_PID FRONTEND_PID < .openclaw_pids.txt
        echo "Stopping processes..."
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
        rm .openclaw_pids.txt
    fi
    
    # Stop Docker containers
    echo "Stopping Docker containers..."
    docker-compose down
    
    echo ""
    echo "✅ System Stopped!"
}

# Main
if [ "$ACTION" = "stop" ]; then
    stop_openclaw
else
    start_openclaw
fi
