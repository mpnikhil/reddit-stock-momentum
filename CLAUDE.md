# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Starting the Application
- `./start-all.sh` - Start both backend and frontend services with one command
- `./start-backend.sh` - Start only the backend FastAPI server
- `./start-frontend.sh` - Start only the React frontend

### Python 3.13 Compatibility
- Updated requirements.txt to use pandas>=2.2.0 and other compatible versions
- If backend fails with pandas compilation errors on Python 3.13, remove venv: `rm -rf backend/venv`

### Frontend Commands (from `/frontend` directory)
- `npm run dev` - Start development server (localhost:3000)
- `npm run build` - Build production bundle with TypeScript compilation
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint with TypeScript rules

### Backend Commands (from `/backend` directory)
- `uvicorn main:app --host 0.0.0.0 --port 8000 --reload` - Start FastAPI server
- `python -c "from app.database import Base, engine, init_db; Base.metadata.create_all(bind=engine); init_db()"` - Initialize database
- Virtual environment is automatically created in `backend/venv/`

## Architecture Overview

### Full-Stack Application
This is a Reddit stock momentum monitoring system with a Python FastAPI backend and React TypeScript frontend.

**Backend (FastAPI + SQLAlchemy):**
- `main.py` - Application entry point with CORS and scheduler initialization
- `app/api.py` - All REST API endpoints for stock data, trending analysis, sentiment
- `app/database.py` - SQLAlchemy models and database session management
- `app/reddit_client.py` - PRAW wrapper for Reddit API interactions
- `app/sentiment_analyzer.py` - NLTK VADER-based sentiment analysis
- `app/stock_detector.py` - AI-powered stock ticker detection in posts
- `app/trend_analyzer.py` - Momentum calculation and trend analysis
- `app/scheduler.py` - APScheduler background jobs for data collection

**Frontend (React + TypeScript + Vite):**
- `src/pages/` - Main page components (Dashboard, Search, Settings, StockDetail)
- `src/components/` - Reusable UI components with Chart.js visualizations
- `src/hooks/useApi.ts` - Custom hook for API calls with error handling
- `src/utils/api.ts` - Centralized API client configuration

### Data Flow
1. **Collection**: APScheduler runs background jobs every 30 minutes to scrape Reddit posts
2. **Processing**: Stock ticker detection and sentiment analysis on collected posts
3. **Analysis**: Trend calculation using momentum scores and volume spike detection
4. **Storage**: SQLite database with proper indexing for efficient queries
5. **API**: FastAPI serves processed data with filtering and aggregation
6. **Frontend**: React app consumes API data and renders interactive charts

### Key APIs
- `/api/trending` - Get trending stocks with momentum and sentiment data
- `/api/stocks/{symbol}` - Detailed stock information with trend history
- `/api/momentum-spikes` - Detect unusual activity spikes
- `/api/search` - Search stocks by symbol or company name
- `/api/sentiment-summary` - Aggregate sentiment analysis across stocks
- `/api/stats` - System statistics and Reddit API status

## Configuration

### Reddit API Setup Required
Before running, copy `backend/config/config.example.yaml` to `backend/config/config.yaml` and add Reddit API credentials from https://www.reddit.com/prefs/apps

### Default Monitored Subreddits
- r/stocks, r/investing, r/SecurityAnalysis, r/ValueInvesting
- r/StockMarket, r/options, r/wallstreetbets, r/financialindependence

### Database
- SQLite database automatically created in `backend/data/reddit_stocks.db`
- Database schema initialized on first run
- Models: Post, Stock, StockMention, DailyTrend, Subreddit

## Background Processing
- Automated Reddit data collection every 30 minutes
- Post processing and stock detection every 15 minutes  
- Trend calculation and momentum analysis every 60 minutes
- NLTK VADER sentiment analysis with financial context
- Scheduler can be disabled with `DISABLE_SCHEDULER=true` environment variable