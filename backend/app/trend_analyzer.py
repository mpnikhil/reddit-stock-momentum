import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, desc, or_, case
from dataclasses import dataclass

from app.database import SessionLocal, DailyTrend, StockMention, Post, Stock, Comment

logger = logging.getLogger(__name__)

@dataclass
class TrendData:
    symbol: str
    date: datetime
    mention_count: int
    unique_posts: int
    avg_sentiment: float
    momentum_score: float
    volume_spike: float

class TrendAnalyzer:
    def __init__(self):
        self.min_mentions_for_trend = 3  # Minimum mentions to consider for trending
        self.lookback_days = 30  # Days to look back for momentum calculation
    
    def calculate_daily_trends(self, target_date: Optional[datetime] = None) -> Dict[str, int]:
        """
        Calculate daily trend data for all stocks
        
        Args:
            target_date: Date to calculate trends for (defaults to today)
            
        Returns:
            Dictionary with calculation statistics
        """
        if target_date is None:
            # Look at yesterday's data since posts may be from different timezone
            target_date = (datetime.utcnow() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        db = SessionLocal()
        stats = {"stocks_processed": 0, "trends_created": 0, "trends_updated": 0}
        
        try:
            # Get all stocks that have mentions in the target date
            start_date = target_date
            end_date = target_date + timedelta(days=1)
            
            # Query mentions for the target date grouped by stock
            # Include both post and comment mentions
            
            mentions_query = db.query(
                StockMention.stock_symbol,
                func.count(StockMention.id).label('mention_count'),
                func.count(func.distinct(
                    case(
                        (StockMention.post_id.isnot(None), StockMention.post_id),
                        else_=StockMention.comment_id
                    )
                )).label('unique_sources'),
                func.avg(StockMention.sentiment_score).label('avg_sentiment')
            ).outerjoin(Post, StockMention.post_id == Post.id
            ).outerjoin(Comment, StockMention.comment_id == Comment.id
            ).filter(
                or_(
                    Post.created_time.between(start_date, end_date),
                    Comment.created_time.between(start_date, end_date)
                )
            ).group_by(StockMention.stock_symbol).all()
            
            for result in mentions_query:
                symbol = result.stock_symbol
                mention_count = result.mention_count
                unique_posts = result.unique_sources
                avg_sentiment = float(result.avg_sentiment) if result.avg_sentiment else 0.0
                
                # Skip if below minimum threshold (but allow lower threshold for daily trends)
                if mention_count < 1:  # Changed from 3 to 1 to capture all activity
                    continue
                
                # Calculate momentum score
                momentum_score = self._calculate_momentum_score(symbol, target_date, db)
                
                # Calculate volume spike (temporarily disabled due to SQL issue)
                volume_spike = 0.0  # self._calculate_volume_spike(symbol, target_date, db)
                
                # Check if trend already exists for this date
                existing_trend = db.query(DailyTrend).filter(
                    DailyTrend.stock_symbol == symbol,
                    DailyTrend.date == target_date
                ).first()
                
                if existing_trend:
                    # Update existing trend
                    existing_trend.mention_count = mention_count
                    existing_trend.unique_posts = unique_posts
                    existing_trend.avg_sentiment = avg_sentiment
                    existing_trend.momentum_score = momentum_score
                    existing_trend.volume_spike = volume_spike
                    stats["trends_updated"] += 1
                else:
                    # Create new trend
                    new_trend = DailyTrend(
                        date=target_date,
                        stock_symbol=symbol,
                        mention_count=mention_count,
                        unique_posts=unique_posts,
                        avg_sentiment=avg_sentiment,
                        momentum_score=momentum_score,
                        volume_spike=volume_spike
                    )
                    db.add(new_trend)
                    stats["trends_created"] += 1
                
                stats["stocks_processed"] += 1
            
            db.commit()
            logger.info(f"Daily trends calculated: {stats}")
            
        except Exception as e:
            logger.error(f"Error calculating daily trends: {e}")
            db.rollback()
        finally:
            db.close()
        
        return stats
    
    def _calculate_momentum_score(self, symbol: str, target_date: datetime, db) -> float:
        """
        Calculate momentum score based on mention count changes over time
        
        Returns:
            Momentum score (higher = more momentum)
        """
        try:
            # Get mention counts for the last N days
            lookback_date = target_date - timedelta(days=self.lookback_days)
            
            daily_counts = db.query(
                func.date(
                    case(
                        (StockMention.post_id.isnot(None), Post.created_time),
                        else_=Comment.created_time
                    )
                ).label('date'),
                func.count(StockMention.id).label('count')
            ).outerjoin(Post, StockMention.post_id == Post.id
            ).outerjoin(Comment, StockMention.comment_id == Comment.id
            ).filter(
                StockMention.stock_symbol == symbol,
                or_(
                    Post.created_time.between(lookback_date, target_date + timedelta(days=1)),
                    Comment.created_time.between(lookback_date, target_date + timedelta(days=1))
                )
            ).group_by(func.date(
                case(
                    (StockMention.post_id.isnot(None), Post.created_time),
                    else_=Comment.created_time
                )
            )).all()
            
            if len(daily_counts) < 1:  # Need at least 1 day of data
                return 0.0
            
            # Convert to list of counts
            counts = [result.count for result in daily_counts]
            
            # Calculate momentum using weighted moving average
            momentum = self._calculate_weighted_momentum(counts)
            
            return momentum
            
        except Exception as e:
            logger.error(f"Error calculating momentum for {symbol}: {e}")
            return 0.0
    
    def _calculate_weighted_momentum(self, counts: List[int]) -> float:
        """
        Calculate weighted momentum score from daily counts
        
        Recent days have higher weights
        """
        if len(counts) < 2:
            return 0.0
        
        # Create weights (more recent = higher weight)
        weights = [i + 1 for i in range(len(counts))]
        total_weight = sum(weights)
        
        # Calculate weighted average for recent period vs older period
        mid_point = len(counts) // 2
        
        if mid_point == 0:
            return 0.0
        
        # Recent period (higher weights)
        recent_counts = counts[mid_point:]
        recent_weights = weights[mid_point:]
        recent_avg = sum(c * w for c, w in zip(recent_counts, recent_weights)) / sum(recent_weights)
        
        # Older period (lower weights)
        older_counts = counts[:mid_point]
        older_weights = weights[:mid_point]
        older_avg = sum(c * w for c, w in zip(older_counts, older_weights)) / sum(older_weights)
        
        # Calculate momentum as percentage change
        if older_avg == 0:
            return min(recent_avg * 10, 100.0)  # Cap very high momentum
        
        momentum = ((recent_avg - older_avg) / older_avg) * 100
        
        # Apply logarithmic scaling for very high values
        if abs(momentum) > 50:
            momentum = 50 * (1 if momentum > 0 else -1) + 10 * (momentum - 50 * (1 if momentum > 0 else -1)) / abs(momentum - 50)
        
        return max(-100.0, min(100.0, momentum))
    
    def _calculate_volume_spike(self, symbol: str, target_date: datetime, db) -> float:
        """
        Calculate volume spike as percentage change from average
        
        Returns:
            Percentage change from average volume
        """
        try:
            # Get current day's mention count (from both posts and comments)
            current_count = db.query(func.count(StockMention.id)
            ).outerjoin(Post, StockMention.post_id == Post.id
            ).outerjoin(Comment, StockMention.comment_id == Comment.id
            ).filter(
                StockMention.stock_symbol == symbol,
                or_(
                    Post.created_time.between(target_date, target_date + timedelta(days=1)),
                    Comment.created_time.between(target_date, target_date + timedelta(days=1))
                )
            ).scalar() or 0
            
            # Get average over last 14 days (excluding current day)
            lookback_start = target_date - timedelta(days=14)
            lookback_end = target_date
            
            avg_count = db.query(func.avg(
                func.count(StockMention.id)
            )).select_from(
                db.query(
                    func.date(Post.created_time).label('date'),
                    func.count(StockMention.id)
                ).join(StockMention).filter(
                    StockMention.stock_symbol == symbol,
                    Post.created_time >= lookback_start,
                    Post.created_time < lookback_end
                ).group_by(func.date(Post.created_time)).subquery()
            ).scalar() or 1
            
            # Calculate percentage change
            if avg_count == 0:
                return 0.0 if current_count == 0 else 100.0
            
            spike = ((current_count - avg_count) / avg_count) * 100
            return max(-100.0, min(500.0, spike))  # Cap at 500% spike
            
        except Exception as e:
            logger.error(f"Error calculating volume spike for {symbol}: {e}")
            return 0.0
    
    def update_momentum_scores(self) -> Dict[str, int]:
        """
        Update momentum scores for recent trends
        
        Returns:
            Dictionary with update statistics
        """
        db = SessionLocal()
        stats = {"trends_updated": 0}
        
        try:
            # Get trends from the last 7 days that need momentum updates
            recent_date = datetime.utcnow() - timedelta(days=7)
            
            trends = db.query(DailyTrend).filter(
                DailyTrend.date >= recent_date
            ).all()
            
            for trend in trends:
                new_momentum = self._calculate_momentum_score(
                    trend.stock_symbol, trend.date, db
                )
                
                if abs(trend.momentum_score - new_momentum) > 1.0:  # Only update if significant change
                    trend.momentum_score = new_momentum
                    stats["trends_updated"] += 1
            
            db.commit()
            logger.info(f"Updated momentum scores: {stats}")
            
        except Exception as e:
            logger.error(f"Error updating momentum scores: {e}")
            db.rollback()
        finally:
            db.close()
        
        return stats
    
    def get_trending_stocks(self, days: int = 1, limit: int = 20) -> List[Dict]:
        """
        Get currently trending stocks based on momentum and volume
        
        Args:
            days: Number of recent days to consider
            limit: Maximum number of stocks to return
            
        Returns:
            List of trending stock dictionaries
        """
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Query trending stocks with their latest trend data
            trending = db.query(
                DailyTrend.stock_symbol,
                Stock.company_name,
                func.sum(DailyTrend.mention_count).label('total_mentions'),
                func.sum(DailyTrend.unique_posts).label('total_posts'),
                func.avg(DailyTrend.avg_sentiment).label('avg_sentiment'),
                func.max(DailyTrend.momentum_score).label('max_momentum'),
                func.max(DailyTrend.volume_spike).label('max_spike'),
                func.max(DailyTrend.date).label('latest_date')
            ).join(Stock).filter(
                DailyTrend.date >= cutoff_date
            ).group_by(
                DailyTrend.stock_symbol, Stock.company_name
            ).order_by(
                desc('max_momentum'),  # Primary sort by momentum
                desc('total_mentions')  # Secondary sort by mentions
            ).limit(limit).all()
            
            results = []
            for row in trending:
                results.append({
                    "symbol": row.stock_symbol,
                    "company_name": row.company_name,
                    "total_mentions": row.total_mentions,
                    "total_posts": row.total_posts,
                    "avg_sentiment": float(row.avg_sentiment) if row.avg_sentiment else 0.0,
                    "momentum_score": float(row.max_momentum),
                    "volume_spike": float(row.max_spike),
                    "latest_date": row.latest_date.isoformat()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting trending stocks: {e}")
            return []
        finally:
            db.close()
    
    def get_stock_trend_history(self, symbol: str, days: int = 30) -> List[Dict]:
        """
        Get trend history for a specific stock
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back
            
        Returns:
            List of trend data points
        """
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            trends = db.query(DailyTrend).filter(
                DailyTrend.stock_symbol == symbol,
                DailyTrend.date >= cutoff_date
            ).order_by(DailyTrend.date).all()
            
            return [
                {
                    "date": trend.date.isoformat(),
                    "mention_count": trend.mention_count,
                    "unique_posts": trend.unique_posts,
                    "avg_sentiment": float(trend.avg_sentiment),
                    "momentum_score": float(trend.momentum_score),
                    "volume_spike": float(trend.volume_spike)
                }
                for trend in trends
            ]
            
        except Exception as e:
            logger.error(f"Error getting trend history for {symbol}: {e}")
            return []
        finally:
            db.close()
    
    def detect_momentum_spikes(self, threshold: float = 50.0) -> List[Dict]:
        """
        Detect stocks with significant momentum spikes in the last 24 hours
        
        Args:
            threshold: Minimum momentum score to be considered a spike
            
        Returns:
            List of stocks with momentum spikes
        """
        db = SessionLocal()
        try:
            recent_date = datetime.utcnow() - timedelta(days=1)
            
            spikes = db.query(
                DailyTrend.stock_symbol,
                Stock.company_name,
                DailyTrend.momentum_score,
                DailyTrend.volume_spike,
                DailyTrend.mention_count,
                DailyTrend.avg_sentiment,
                DailyTrend.date
            ).join(Stock).filter(
                DailyTrend.date >= recent_date,
                DailyTrend.momentum_score >= threshold
            ).order_by(desc(DailyTrend.momentum_score)).all()
            
            return [
                {
                    "symbol": spike.stock_symbol,
                    "company_name": spike.company_name,
                    "momentum_score": float(spike.momentum_score),
                    "volume_spike": float(spike.volume_spike),
                    "mention_count": spike.mention_count,
                    "avg_sentiment": float(spike.avg_sentiment),
                    "date": spike.date.isoformat()
                }
                for spike in spikes
            ]
            
        except Exception as e:
            logger.error(f"Error detecting momentum spikes: {e}")
            return []
        finally:
            db.close()