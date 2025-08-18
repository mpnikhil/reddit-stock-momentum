# Reddit Stock Momentum Monitor - Setup Guide

This guide will help you set up and run the Reddit Stock Momentum Monitor on your local Mac system.

## Prerequisites

Before starting, ensure you have the following installed:

### Required Software
- **Python 3.9+**: Download from [python.org](https://www.python.org/downloads/)
- **Node.js 16+**: Download from [nodejs.org](https://nodejs.org/)
- **Git**: Usually pre-installed on macOS

### Verify Installation
```bash
python3 --version  # Should show 3.9+
node --version      # Should show v16+
npm --version       # Should show npm version
```

## Step 1: Reddit API Setup

You need Reddit API credentials to collect data:

1. **Create a Reddit Account** (if you don't have one)
   - Go to [reddit.com](https://reddit.com) and create an account

2. **Create a Reddit App**
   - Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
   - Click "Create App" or "Create Another App"
   - Fill in the form:
     - **Name**: `Stock Momentum Monitor` (or any name)
     - **App type**: Select "script"
     - **Description**: Optional
     - **About URL**: Leave blank
     - **Redirect URI**: `http://localhost:8000` (required but not used)
   - Click "Create app"

3. **Save Your Credentials**
   - After creating the app, you'll see:
     - **Client ID**: String under the app name (looks like `abc123xyz`)
     - **Client Secret**: Longer string labeled "secret"
   - Keep these safe - you'll need them in Step 3!

## Step 2: Project Setup

1. **Navigate to the Project Directory**
   ```bash
   cd /Users/nikhilpujari/reddit-scraper
   ```

2. **Verify Project Structure**
   ```bash
   ls -la
   ```
   You should see:
   - `backend/` - Python FastAPI backend
   - `frontend/` - React frontend
   - `start-*.sh` - Startup scripts
   - `README.md` - Project documentation

## Step 3: Configuration

### Option A: Using Configuration File (Recommended)

1. **Copy the Example Configuration**
   ```bash
   cp backend/config/config.example.yaml backend/config/config.yaml
   ```

2. **Edit the Configuration**
   ```bash
   open backend/config/config.yaml
   ```
   
3. **Update Reddit Credentials**
   Replace the placeholder values:
   ```yaml
   reddit:
     client_id: "your_actual_client_id_here"
     client_secret: "your_actual_client_secret_here"
     user_agent: "StockMomentumMonitor/1.0 by YourRedditUsername"
   ```

### Option B: Using Environment Variables

1. **Copy the Example Environment File**
   ```bash
   cp backend/.env.example backend/.env
   ```

2. **Edit the Environment File**
   ```bash
   open backend/.env
   ```
   
3. **Update Reddit Credentials**
   ```bash
   REDDIT_CLIENT_ID=your_actual_client_id_here
   REDDIT_CLIENT_SECRET=your_actual_client_secret_here
   REDDIT_USER_AGENT=StockMomentumMonitor/1.0
   ```

## Step 4: Installation and Startup

### Quick Start (Recommended)
Run everything with one command:
```bash
./start-all.sh
```

This will:
- Set up Python virtual environment
- Install all dependencies
- Initialize the database
- Start both backend and frontend
- Open your browser automatically

### Manual Start (For Development)

If you prefer to start services individually:

1. **Start Backend** (Terminal 1)
   ```bash
   ./start-backend.sh
   ```

2. **Start Frontend** (Terminal 2)
   ```bash
   ./start-frontend.sh
   ```

## Step 5: Verify Everything Works

1. **Check Backend**
   - Open [http://localhost:8000](http://localhost:8000)
   - You should see: `{"message": "Reddit Stock Momentum Monitor API", "status": "running"}`

2. **Check API Documentation**
   - Open [http://localhost:8000/docs](http://localhost:8000/docs)
   - You should see the interactive API documentation

3. **Check Frontend**
   - Open [http://localhost:3000](http://localhost:3000)
   - You should see the dashboard interface

4. **Test Data Collection**
   - Go to Settings page in the frontend
   - Click "Trigger" next to "Collect Reddit Data" job
   - Wait a few minutes, then check the dashboard for trending stocks

## Step 6: Understanding the System

### How It Works
1. **Data Collection**: Every 30 minutes, the system collects posts from monitored subreddits
2. **Stock Detection**: AI identifies stock ticker symbols in post content
3. **Sentiment Analysis**: Each mention is analyzed for positive/negative sentiment
4. **Trend Calculation**: System calculates momentum scores and volume spikes
5. **Dashboard Updates**: Frontend displays trending stocks and charts

### Monitored Subreddits
By default, the system monitors:
- r/stocks
- r/investing
- r/SecurityAnalysis
- r/ValueInvesting
- r/StockMarket
- r/pennystocks
- r/options
- r/wallstreetbets
- r/financialindependence

### Key Features
- **Real-time Dashboard**: See trending stocks and momentum
- **Interactive Charts**: Visualize trends over time
- **Sentiment Analysis**: Understand market sentiment
- **Search Functionality**: Find specific stocks
- **Data Export**: Download data for analysis

## Troubleshooting

### Backend Won't Start
1. **Check Python Version**
   ```bash
   python3 --version
   ```
   Must be 3.9 or higher

2. **Check Reddit Credentials**
   - Verify config.yaml has correct client_id and client_secret
   - Make sure they're not the placeholder values

3. **Check Logs**
   ```bash
   tail -f backend.log
   ```

### Frontend Won't Start
1. **Check Node Version**
   ```bash
   node --version
   ```
   Must be v16 or higher

2. **Clear Node Modules**
   ```bash
   cd frontend
   rm -rf node_modules
   npm install
   ```

3. **Check Logs**
   ```bash
   tail -f frontend.log
   ```

### No Data Appearing
1. **Trigger Manual Collection**
   - Go to Settings page
   - Click "Trigger" next to data collection jobs

2. **Check Reddit API Limits**
   - API rate limits may be reached
   - Wait an hour and try again

3. **Verify Subreddit Access**
   - Some subreddits may be private
   - Check that your Reddit account has access

### Performance Issues
1. **Database Size**
   - SQLite database grows over time
   - Use data export to archive old data

2. **Memory Usage**
   - Restart the backend periodically
   - Monitor system resources

## Advanced Configuration

### Customizing Subreddits
Edit `backend/config/config.yaml`:
```yaml
subreddits:
  default_active:
    - stocks
    - investing
    # Add your custom subreddits here
```

### Adjusting Collection Frequency
```yaml
app:
  scheduler:
    reddit_collection_interval: 30  # minutes
    post_processing_interval: 15    # minutes
    trend_calculation_interval: 60  # minutes
```

### Data Retention Settings
```yaml
app:
  data_retention:
    keep_posts_days: 90     # Keep posts for 90 days
    keep_trends_days: 365   # Keep trends for 1 year
```

## Getting Help

If you encounter issues:

1. **Check the logs** in `backend.log` and `frontend.log`
2. **Verify your Reddit API credentials**
3. **Ensure all dependencies are installed**
4. **Check that ports 3000 and 8000 are available**

## Next Steps

Once everything is running:

1. **Explore the Dashboard** - See trending stocks and momentum
2. **Check Individual Stocks** - Click on stocks for detailed analysis
3. **Use Search** - Find specific stocks you're interested in
4. **Monitor Settings** - Keep an eye on data collection status
5. **Export Data** - Download trending data for external analysis

Enjoy tracking stock momentum across Reddit! 🚀📈