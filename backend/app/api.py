from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.database import get_db, Post, Stock, StockMention, DailyTrend, Subreddit
from app.trend_analyzer import TrendAnalyzer
from app.sentiment_analyzer import sentiment_analyzer
from app.reddit_client import reddit_client
from app import scheduler

router = APIRouter()
trend_analyzer = TrendAnalyzer()

@router.get("/trending")
async def get_trending_stocks(
    days: int = Query(default=1, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of stocks to return"),
    min_mentions: int = Query(default=5, ge=1, description="Minimum mentions required"),
    db: Session = Depends(get_db)
):
    """Get currently trending stocks based on momentum and volume"""
    try:
        trending_stocks = trend_analyzer.get_trending_stocks(days=days, limit=limit)
        
        # Filter by minimum mentions
        filtered_stocks = [
            stock for stock in trending_stocks 
            if stock["total_mentions"] >= min_mentions
        ]
        
        return {
            "trending_stocks": filtered_stocks,
            "total_count": len(filtered_stocks),
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving trending stocks: {str(e)}")

@router.get("/stocks/{symbol}")
async def get_stock_details(
    symbol: str,
    days: int = Query(default=7, ge=1, le=90, description="Number of days for trend history"),
    db: Session = Depends(get_db)
):
    """Get detailed information for a specific stock"""
    try:
        symbol = symbol.upper()
        
        # Get stock info
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        
        # Get trend history
        trend_history = trend_analyzer.get_stock_trend_history(symbol, days=days)
        
        # Get sentiment summary
        sentiment_summary = sentiment_analyzer.get_stock_sentiment_summary(symbol, days=days)
        
        # Get recent posts mentioning this stock
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        recent_posts = db.query(
            Post.id, Post.title, Post.subreddit, Post.created_time, 
            Post.score, StockMention.sentiment_score
        ).join(StockMention).filter(
            StockMention.stock_symbol == symbol,
            Post.created_time >= cutoff_date
        ).order_by(desc(Post.created_time)).limit(10).all()
        
        posts_data = [
            {
                "id": post.id,
                "title": post.title,
                "subreddit": post.subreddit,
                "created_time": post.created_time.isoformat(),
                "score": post.score,
                "sentiment_score": float(post.sentiment_score) if post.sentiment_score else None
            }
            for post in recent_posts
        ]
        
        return {
            "symbol": symbol,
            "company_name": stock.company_name,
            "market_cap": stock.market_cap,
            "sector": stock.sector,
            "trend_history": trend_history,
            "sentiment_summary": sentiment_summary,
            "recent_posts": posts_data,
            "data_period_days": days
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stock details: {str(e)}")

@router.get("/stocks/{symbol}/mentions")
async def get_stock_mentions(
    symbol: str,
    days: int = Query(default=7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of mentions to return"),
    db: Session = Depends(get_db)
):
    """Get detailed mentions for a specific stock"""
    try:
        symbol = symbol.upper()
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        mentions = db.query(
            StockMention.id,
            StockMention.mention_count,
            StockMention.sentiment_score,
            StockMention.context_snippet,
            StockMention.created_at,
            Post.id.label('post_id'),
            Post.title,
            Post.subreddit,
            Post.created_time,
            Post.score,
            Post.url
        ).join(Post).filter(
            StockMention.stock_symbol == symbol,
            Post.created_time >= cutoff_date
        ).order_by(desc(Post.created_time)).limit(limit).all()
        
        mentions_data = [
            {
                "mention_id": mention.id,
                "post_id": mention.post_id,
                "post_title": mention.title,
                "subreddit": mention.subreddit,
                "mention_count": mention.mention_count,
                "sentiment_score": float(mention.sentiment_score) if mention.sentiment_score else None,
                "context_snippet": mention.context_snippet,
                "created_time": mention.created_time.isoformat(),
                "post_score": mention.score,
                "post_url": mention.url
            }
            for mention in mentions
        ]
        
        return {
            "symbol": symbol,
            "mentions": mentions_data,
            "total_mentions": len(mentions_data),
            "period_days": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stock mentions: {str(e)}")

@router.get("/momentum-spikes")
async def get_momentum_spikes(
    threshold: float = Query(default=50.0, ge=10.0, description="Minimum momentum score threshold"),
    db: Session = Depends(get_db)
):
    """Get stocks with significant momentum spikes"""
    try:
        spikes = trend_analyzer.detect_momentum_spikes(threshold=threshold)
        
        return {
            "momentum_spikes": spikes,
            "threshold": threshold,
            "total_spikes": len(spikes),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting momentum spikes: {str(e)}")

@router.get("/subreddits")
async def get_monitored_subreddits(db: Session = Depends(get_db)):
    """Get list of monitored subreddits with statistics"""
    try:
        subreddits = db.query(Subreddit).all()
        
        subreddit_data = []
        for subreddit in subreddits:
            # Get recent post count
            recent_posts = db.query(func.count(Post.id)).filter(
                Post.subreddit == subreddit.name,
                Post.created_time >= datetime.utcnow() - timedelta(days=7)
            ).scalar() or 0
            
            subreddit_data.append({
                "name": subreddit.name,
                "display_name": subreddit.display_name,
                "is_active": bool(subreddit.is_active),
                "subscribers": subreddit.subscribers,
                "last_scraped": subreddit.last_scraped.isoformat() if subreddit.last_scraped else None,
                "total_posts_collected": subreddit.posts_collected,
                "recent_posts_7d": recent_posts
            })
        
        return {
            "subreddits": subreddit_data,
            "total_subreddits": len(subreddit_data),
            "active_subreddits": len([s for s in subreddit_data if s["is_active"]])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving subreddits: {str(e)}")

@router.get("/search")
async def search_stocks(
    query: str = Query(..., min_length=1, description="Search query (symbol or company name)"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """Search stocks by symbol or company name"""
    try:
        query = query.upper().strip()
        
        # Search by symbol or company name
        stocks = db.query(Stock).filter(
            (Stock.symbol.like(f"%{query}%")) |
            (Stock.company_name.ilike(f"%{query}%"))
        ).limit(limit).all()
        
        results = []
        for stock in stocks:
            # Get recent mention count
            recent_mentions = db.query(func.count(StockMention.id)).join(Post).filter(
                StockMention.stock_symbol == stock.symbol,
                Post.created_time >= datetime.utcnow() - timedelta(days=7)
            ).scalar() or 0
            
            results.append({
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "market_cap": stock.market_cap,
                "sector": stock.sector,
                "recent_mentions_7d": recent_mentions
            })
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching stocks: {str(e)}")

@router.get("/sentiment-summary")
async def get_sentiment_summary(
    days: int = Query(default=7, ge=1, le=30, description="Number of days to analyze"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum stocks to return"),
    db: Session = Depends(get_db)
):
    """Get sentiment summary across all stocks"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get sentiment data grouped by stock
        sentiment_data = db.query(
            StockMention.stock_symbol,
            Stock.company_name,
            func.count(StockMention.id).label('mention_count'),
            func.avg(StockMention.sentiment_score).label('avg_sentiment'),
            func.min(StockMention.sentiment_score).label('min_sentiment'),
            func.max(StockMention.sentiment_score).label('max_sentiment')
        ).join(Stock).join(Post).filter(
            Post.created_time >= cutoff_date,
            StockMention.sentiment_score.isnot(None)
        ).group_by(
            StockMention.stock_symbol, Stock.company_name
        ).order_by(
            desc('mention_count')
        ).limit(limit).all()
        
        results = []
        for row in sentiment_data:
            avg_sentiment = float(row.avg_sentiment) if row.avg_sentiment else 0.0
            
            # Classify sentiment
            if avg_sentiment > 0.1:
                sentiment_label = "Positive"
            elif avg_sentiment < -0.1:
                sentiment_label = "Negative"
            else:
                sentiment_label = "Neutral"
            
            results.append({
                "symbol": row.stock_symbol,
                "company_name": row.company_name,
                "mention_count": row.mention_count,
                "avg_sentiment": avg_sentiment,
                "min_sentiment": float(row.min_sentiment) if row.min_sentiment else 0.0,
                "max_sentiment": float(row.max_sentiment) if row.max_sentiment else 0.0,
                "sentiment_label": sentiment_label
            })
        
        return {
            "sentiment_summary": results,
            "period_days": days,
            "total_stocks": len(results),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sentiment summary: {str(e)}")

@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Get overall system statistics"""
    try:
        # Basic counts
        total_posts = db.query(func.count(Post.id)).scalar() or 0
        total_stocks = db.query(func.count(Stock.symbol)).scalar() or 0
        total_mentions = db.query(func.count(StockMention.id)).scalar() or 0
        
        # Recent activity (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_posts = db.query(func.count(Post.id)).filter(
            Post.created_time >= recent_cutoff
        ).scalar() or 0
        
        recent_mentions = db.query(func.count(StockMention.id)).join(Post).filter(
            Post.created_time >= recent_cutoff
        ).scalar() or 0
        
        # Top subreddits by recent activity
        top_subreddits = db.query(
            Post.subreddit,
            func.count(Post.id).label('post_count')
        ).filter(
            Post.created_time >= recent_cutoff
        ).group_by(Post.subreddit).order_by(desc('post_count')).limit(5).all()
        
        # Reddit API status
        api_limits = reddit_client.get_api_limits()
        
        return {
            "total_posts": total_posts,
            "total_stocks": total_stocks,
            "total_mentions": total_mentions,
            "recent_24h": {
                "posts": recent_posts,
                "mentions": recent_mentions
            },
            "top_subreddits_24h": [
                {"subreddit": sub.subreddit, "posts": sub.post_count}
                for sub in top_subreddits
            ],
            "reddit_api_status": api_limits,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving system stats: {str(e)}")

@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get background scheduler status"""
    try:
        status = scheduler.get_scheduler_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving scheduler status: {str(e)}")

@router.post("/scheduler/trigger/{job_id}")
async def trigger_scheduler_job(job_id: str):
    """Manually trigger a scheduler job"""
    try:
        success = scheduler.trigger_job(job_id)
        if success:
            return {"message": f"Job {job_id} triggered successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering job: {str(e)}")

@router.get("/export/trending")
async def export_trending_data(
    days: int = Query(default=7, ge=1, le=30, description="Number of days to export"),
    format: str = Query(default="json", regex="^(json|csv)$", description="Export format")
):
    """Export trending data for analysis"""
    try:
        trending_stocks = trend_analyzer.get_trending_stocks(days=days, limit=100)
        
        if format == "csv":
            import io
            import csv
            from fastapi.responses import StreamingResponse
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'symbol', 'company_name', 'total_mentions', 'total_posts',
                'avg_sentiment', 'momentum_score', 'volume_spike', 'latest_date'
            ])
            writer.writeheader()
            writer.writerows(trending_stocks)
            
            response = StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=trending_stocks_{days}d.csv"}
            )
            return response
        
        return {
            "export_data": trending_stocks,
            "period_days": days,
            "total_stocks": len(trending_stocks),
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")