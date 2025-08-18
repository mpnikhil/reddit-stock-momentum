# Reddit Stock Momentum Monitor

A comprehensive system for tracking stock discussions across Reddit to identify trending stocks and emerging momentum patterns. Built for local Mac development with a focus on ease of use and powerful analytics.

## ✨ Features

- **🔍 Multi-subreddit monitoring**: Tracks discussions across r/stocks, r/investing, r/wallstreetbets, and more
- **🤖 Smart stock detection**: AI-powered parsing of ticker symbols and company names with context awareness
- **💭 Real-time sentiment analysis**: VADER-based sentiment scoring enhanced for financial terminology
- **📈 Trend analysis**: Momentum tracking and anomaly detection for unusual activity spikes
- **📊 Interactive dashboard**: Clean, responsive UI with filtering, charts, and time-based views
- **🔎 Search functionality**: Find specific stocks and analyze their discussion history
- **📤 Export functionality**: Download trending data in CSV/JSON format for further analysis
- **⚙️ Background processing**: Automated data collection every 30 minutes with configurable schedules

## 🚀 Quick Start

### Prerequisites
- macOS (optimized for local Mac development)
- Python 3.9+ ([Download](https://www.python.org/downloads/))
- Node.js 16+ ([Download](https://nodejs.org/))
- Reddit API credentials ([Get here](https://www.reddit.com/prefs/apps))

### One-Line Setup
```bash
./start-all.sh
```

This single command will:
- Set up Python virtual environment
- Install all dependencies 
- Initialize the database
- Configure NLTK for sentiment analysis
- Start both backend and frontend
- Open the dashboard in your browser

### Manual Setup (Alternative)

1. **Get Reddit API Credentials**:
   - Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
   - Create a new app (type: script)
   - Note your client_id and client_secret

2. **Configure the Application**:
   ```bash
   cp backend/config/config.example.yaml backend/config/config.yaml
   # Edit config.yaml with your Reddit credentials
   ```

3. **Start Backend**:
   ```bash
   ./start-backend.sh
   ```

4. **Start Frontend** (in new terminal):
   ```bash
   ./start-frontend.sh
   ```

5. **Access the Application**:
   - 🌐 Frontend Dashboard: [http://localhost:3000](http://localhost:3000)
   - 🔧 Backend API: [http://localhost:8000](http://localhost:8000)
   - 📚 API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📱 How to Use

### Dashboard
- View trending stocks with momentum scores and sentiment analysis
- Filter by time range (1 day to 30 days) and minimum mentions
- See volume spikes and momentum indicators
- Click on stocks for detailed analysis

### Stock Details
- Interactive charts showing mention trends, sentiment over time, and momentum
- Recent posts and detailed mention analysis
- Historical trend data with context

### Search
- Find stocks by ticker symbol or company name
- See recent mention counts and activity levels
- Partial matching supported

### Settings
- Monitor background job status and manually trigger data collection
- View system statistics and Reddit API status
- Export trending data for external analysis
- Manage monitored subreddits

## 🏗️ Architecture

### Backend (Python FastAPI)
- **FastAPI**: Modern, fast web framework with automatic API documentation
- **SQLAlchemy + SQLite**: Lightweight database for local development
- **PRAW**: Python Reddit API Wrapper for data collection
- **NLTK VADER**: Enhanced sentiment analysis for financial content
- **APScheduler**: Background job scheduling for automated data collection

### Frontend (React + TypeScript)
- **React 18**: Modern UI with hooks and concurrent features
- **TypeScript**: Type safety and better developer experience
- **Tailwind CSS**: Utility-first styling for responsive design
- **Chart.js**: Interactive charts for trend visualization
- **Vite**: Fast development server and build tool

### Data Processing Pipeline
1. **Collection**: Automated Reddit post collection every 30 minutes
2. **Detection**: AI-powered stock ticker detection with confidence scoring
3. **Sentiment**: Financial-aware sentiment analysis with custom lexicon
4. **Trends**: Momentum calculation using weighted moving averages
5. **Storage**: Efficient SQLite storage with proper indexing

## 📊 Monitored Subreddits

- r/stocks - General stock discussions
- r/investing - Investment strategies and advice
- r/SecurityAnalysis - In-depth stock analysis
- r/ValueInvesting - Value investing focused content
- r/StockMarket - Market news and discussions
- r/pennystocks - Small cap and penny stock discussions
- r/options - Options trading discussions
- r/wallstreetbets - High-risk trading and meme stocks
- r/financialindependence - Long-term investing for FIRE

*Subreddits can be customized in the configuration file*

## 🔧 Configuration

### Reddit API Setup
1. Create app at [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Choose "script" type
3. Add credentials to `backend/config/config.yaml`

### Customization Options
- **Collection frequency**: Adjust how often data is collected
- **Subreddit list**: Add or remove monitored communities  
- **Detection sensitivity**: Configure stock detection confidence
- **Data retention**: Set how long to keep historical data
- **Rate limits**: Respect Reddit API guidelines

## 📈 Key Metrics

- **Mention Count**: Number of times a stock is mentioned
- **Sentiment Score**: Average sentiment (-1 to +1) across mentions
- **Momentum Score**: Percentage change in mention velocity
- **Volume Spike**: Unusual increase in mention activity
- **Unique Posts**: Number of distinct posts mentioning the stock

## 🛠️ Development

### Project Structure
```
reddit-scraper/
├── backend/           # Python FastAPI backend
│   ├── app/          # Application code
│   ├── config/       # Configuration files
│   └── data/         # SQLite database
├── frontend/         # React frontend
│   ├── src/          # Source code
│   └── public/       # Static assets
├── start-*.sh        # Startup scripts
└── README.md         # This file
```

### API Endpoints
- `GET /api/trending` - Trending stocks with filters
- `GET /api/stocks/{symbol}` - Detailed stock information
- `GET /api/stocks/{symbol}/mentions` - Stock mention history
- `GET /api/momentum-spikes` - Stocks with momentum spikes
- `GET /api/search` - Search stocks by symbol/name
- `GET /api/sentiment-summary` - Sentiment analysis overview
- `GET /api/stats` - System statistics
- `GET /api/subreddits` - Monitored subreddit information

## 📋 Requirements

### System Requirements
- macOS 10.14+ (optimized for Mac)
- 4GB RAM minimum, 8GB recommended
- 1GB free disk space
- Internet connection for Reddit API

### Dependencies
All dependencies are automatically installed by the startup scripts:
- **Backend**: FastAPI, SQLAlchemy, PRAW, NLTK, pandas, APScheduler
- **Frontend**: React, TypeScript, Chart.js, Tailwind CSS, Vite

## 🤝 Contributing

This project is designed for local development and personal use. Feel free to:
- Modify subreddit lists for your interests
- Adjust detection algorithms for better accuracy
- Add new visualizations and charts
- Customize the UI theme and layout
- Extend API endpoints for additional features

## 📞 Support

If you encounter issues:
1. Check the [Setup Guide](SETUP.md) for detailed instructions
2. Review logs in `backend.log` and `frontend.log`
3. Verify Reddit API credentials are correct
4. Ensure ports 3000 and 8000 are available

## 📜 License

This project is for educational and personal use. Please respect Reddit's API terms of service and rate limits.

---

**Built with ❤️ for the Reddit investing community. Track trends, spot opportunities, make informed decisions.** 🚀📈