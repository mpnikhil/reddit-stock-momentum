#!/bin/bash

# Reddit Stock Monitor - Complete Startup Script

echo "🚀 Starting Reddit Stock Monitor (Full Stack)..."
echo ""

# Check if we're on macOS and have the required tools
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Detected macOS system"
    
    # Check for required tools
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is required but not installed."
        echo "   Install from: https://www.python.org/downloads/"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js is required but not installed."
        echo "   Install from: https://nodejs.org/"
        exit 1
    fi
    
    echo "✅ All required tools are available"
    echo ""
fi

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "   Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "   Frontend stopped"
    fi
    echo "👋 Goodbye!"
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Make scripts executable
chmod +x start-backend.sh start-frontend.sh

# Start backend in background
echo "🔧 Starting backend..."
./start-backend.sh > backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 5

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start. Check backend.log for details."
    exit 1
fi

echo "✅ Backend started (PID: $BACKEND_PID)"

# Start frontend in background
echo "🎨 Starting frontend..."
./start-frontend.sh > frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 5

# Check if frontend is running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend failed to start. Check frontend.log for details."
    cleanup
    exit 1
fi

echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo ""
echo "🌟 Reddit Stock Monitor is now running!"
echo ""
echo "📱 Access the application:"
echo "   🌐 Frontend: http://localhost:3000"
echo "   🔧 Backend API: http://localhost:8000"
echo "   📊 API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Configuration:"
echo "   ⚙️  Backend config: backend/config/config.yaml"
echo "   📋 Setup guide: See README.md"
echo ""
echo "📊 Logs:"
echo "   🔧 Backend: backend.log"
echo "   🎨 Frontend: frontend.log"
echo ""
echo "🛑 Press Ctrl+C to stop all services"

# Wait for user to stop services
while true; do
    sleep 1
    
    # Check if processes are still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "⚠️  Backend process stopped unexpectedly"
        break
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "⚠️  Frontend process stopped unexpectedly"
        break
    fi
done

cleanup