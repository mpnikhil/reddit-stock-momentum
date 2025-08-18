#!/bin/bash

# Reddit Stock Monitor - Frontend Startup Script

echo "🎨 Starting Reddit Stock Monitor Frontend..."

# Navigate to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the development server
echo "🌟 Starting React development server..."
echo "🌐 Frontend will be available at: http://localhost:3000"
echo "🔗 Backend API proxy configured for: http://localhost:8000"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo ""

npm run dev