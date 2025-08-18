#!/bin/bash

# Reddit Stock Monitor - Backend Startup Script

echo "🚀 Starting Reddit Stock Monitor Backend..."

# Navigate to backend directory
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs config

# Check for configuration
if [ ! -f "config/config.yaml" ]; then
    echo "⚠️  Configuration file not found!"
    echo "📋 Please copy config/config.example.yaml to config/config.yaml"
    echo "   and configure your Reddit API credentials:"
    echo "   1. Go to https://www.reddit.com/prefs/apps"
    echo "   2. Create a new app (script type)"
    echo "   3. Copy client_id and client_secret to config.yaml"
    echo ""
    echo "🔄 For now, starting with environment variables..."
fi

# Initialize database
echo "🗄️  Initializing database..."
python -c "from app.database import Base, engine, init_db; Base.metadata.create_all(bind=engine); init_db()"

# Download NLTK data for sentiment analysis
echo "🧠 Downloading NLTK data..."
python -c "import nltk; nltk.download('vader_lexicon', quiet=True)"

# Start the server
echo "🌟 Starting FastAPI server..."
echo "📱 Backend will be available at: http://localhost:8000"
echo "📊 API documentation at: http://localhost:8000/docs"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload