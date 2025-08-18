from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from app.reddit_client import reddit_client
from app.stock_detector import stock_detector
from app.sentiment_analyzer import sentiment_analyzer
from app.trend_analyzer import TrendAnalyzer
from app.database import SessionLocal, DailyTrend

logger = logging.getLogger(__name__)

class BackgroundScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.trend_analyzer = TrendAnalyzer()
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Setup all scheduled jobs"""
        
        # Reddit data collection - every 10 minutes
        self.scheduler.add_job(
            func=self._collect_reddit_data,
            trigger=IntervalTrigger(minutes=10),
            id='reddit_collection',
            name='Collect Reddit Data',
            max_instances=1,
            replace_existing=True
        )
        
        # Comment collection - every 15 minutes
        self.scheduler.add_job(
            func=self._collect_comments,
            trigger=IntervalTrigger(minutes=15),
            id='comment_collection',
            name='Collect Comments',
            max_instances=1,
            replace_existing=True
        )
        
        # Stock detection and sentiment analysis - every 5 minutes
        self.scheduler.add_job(
            func=self._process_new_posts,
            trigger=IntervalTrigger(minutes=5),
            id='process_posts',
            name='Process New Posts',
            max_instances=1,
            replace_existing=True
        )
        
        # Trend calculation - every 10 minutes
        self.scheduler.add_job(
            func=self._calculate_trends,
            trigger=IntervalTrigger(minutes=10),
            id='calculate_trends',
            name='Calculate Trends',
            max_instances=1,
            replace_existing=True
        )
        
        # Daily cleanup - at 2 AM every day
        self.scheduler.add_job(
            func=self._daily_cleanup,
            trigger=CronTrigger(hour=2, minute=0),
            id='daily_cleanup',
            name='Daily Cleanup',
            max_instances=1,
            replace_existing=True
        )
        
        # Health check - every 5 minutes
        self.scheduler.add_job(
            func=self._health_check,
            trigger=IntervalTrigger(minutes=5),
            id='health_check',
            name='Health Check',
            max_instances=1,
            replace_existing=True
        )
    
    async def _collect_reddit_data(self):
        """Collect new posts from Reddit"""
        try:
            logger.info("Starting Reddit data collection...")
            
            if not reddit_client.is_connected():
                logger.error("Reddit client not connected")
                return
            
            # Collect from all subreddits
            results = reddit_client.collect_from_all_subreddits(limit_per_subreddit=50)
            
            total_new_posts = sum(results.values())
            logger.info(f"Collected {total_new_posts} new posts: {results}")
            
            # Log API limits
            limits = reddit_client.get_api_limits()
            if "remaining" in limits:
                logger.info(f"Reddit API remaining: {limits['remaining']}")
            
        except Exception as e:
            logger.error(f"Error in Reddit data collection: {e}")
    
    async def _collect_comments(self):
        """Collect comments from recent posts"""
        try:
            logger.info("Starting comment collection...")
            
            if not reddit_client.is_connected():
                logger.error("Reddit client not connected")
                return
            
            # Collect comments for recent posts
            comment_stats = reddit_client.collect_comments_for_recent_posts(
                hours_back=24, max_posts=30
            )
            
            logger.info(f"Comment collection complete: {comment_stats}")
            
        except Exception as e:
            logger.error(f"Error in comment collection: {e}")
    
    async def _process_new_posts(self):
        """Process new posts for stock mentions and sentiment"""
        try:
            logger.info("Processing new posts for stock mentions...")
            
            # Process unprocessed posts for stock mentions
            stock_stats = stock_detector.process_all_unprocessed_posts()
            logger.info(f"Stock detection (posts): {stock_stats}")
            
            # Process unprocessed comments for stock mentions
            comment_stats = stock_detector.process_all_unprocessed_comments()
            logger.info(f"Stock detection (comments): {comment_stats}")
            
            # Update sentiment scores for mentions
            sentiment_stats = sentiment_analyzer.update_mention_sentiments(batch_size=200)
            logger.info(f"Sentiment analysis: {sentiment_stats}")
            
        except Exception as e:
            logger.error(f"Error processing new posts: {e}")
    
    async def _calculate_trends(self):
        """Calculate trend scores and momentum"""
        try:
            logger.info("Calculating stock trends...")
            
            # Calculate trends for the last 7 days to capture all recent activity
            total_stats = {"stocks_processed": 0, "trends_created": 0, "trends_updated": 0}
            for days_back in range(7):
                target_date = (datetime.utcnow() - timedelta(days=days_back)).replace(hour=0, minute=0, second=0, microsecond=0)
                trend_stats = self.trend_analyzer.calculate_daily_trends(target_date)
                for key in total_stats:
                    total_stats[key] += trend_stats.get(key, 0)
            logger.info(f"Trend calculation (3 days): {total_stats}")
            
            # Update momentum scores
            momentum_stats = self.trend_analyzer.update_momentum_scores()
            logger.info(f"Momentum calculation: {momentum_stats}")
            
        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
    
    async def _daily_cleanup(self):
        """Perform daily maintenance tasks"""
        try:
            logger.info("Starting daily cleanup...")
            
            db = SessionLocal()
            
            # Clean up old data (keep last 90 days)
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            # Clean old trends
            old_trends = db.query(DailyTrend).filter(
                DailyTrend.date < cutoff_date
            ).count()
            
            if old_trends > 0:
                db.query(DailyTrend).filter(
                    DailyTrend.date < cutoff_date
                ).delete()
                logger.info(f"Cleaned up {old_trends} old trend records")
            
            db.commit()
            db.close()
            
            # Force garbage collection for long-running process
            import gc
            gc.collect()
            
            logger.info("Daily cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in daily cleanup: {e}")
    
    async def _health_check(self):
        """Perform health checks on system components"""
        try:
            # Check Reddit client
            reddit_health = reddit_client.is_connected()
            
            # Check database connectivity
            db_health = False
            try:
                db = SessionLocal()
                db.execute("SELECT 1")
                db_health = True
                db.close()
            except Exception:
                pass
            
            # Log health status every hour (12 checks per hour)
            current_minute = datetime.now().minute
            if current_minute % 60 == 0:  # Log once per hour
                logger.info(f"Health check - Reddit: {reddit_health}, Database: {db_health}")
            
            # Alert on critical failures
            if not reddit_health:
                logger.warning("Reddit client health check failed")
            if not db_health:
                logger.error("Database health check failed")
                
        except Exception as e:
            logger.error(f"Error in health check: {e}")
    
    def start(self):
        """Start the scheduler"""
        try:
            self.scheduler.start()
            logger.info("Background scheduler started successfully")
            
            # Log next run times
            for job in self.scheduler.get_jobs():
                logger.info(f"Job '{job.name}' next run: {job.next_run_time}")
                
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("Background scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs"""
        jobs_status = []
        
        for job in self.scheduler.get_jobs():
            jobs_status.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "running": job.id in [j.id for j in self.scheduler.get_jobs() if j.next_run_time]
            })
        
        return {
            "scheduler_running": self.scheduler.running,
            "jobs": jobs_status,
            "total_jobs": len(jobs_status)
        }
    
    def trigger_job(self, job_id: str) -> bool:
        """Manually trigger a specific job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                logger.info(f"Triggered job: {job_id}")
                return True
            else:
                logger.warning(f"Job not found: {job_id}")
                return False
        except Exception as e:
            logger.error(f"Error triggering job {job_id}: {e}")
            return False

# Global scheduler instance
scheduler_instance = BackgroundScheduler()

def start_scheduler():
    """Start the background scheduler"""
    try:
        scheduler_instance.start()
        
        # Run initial data collection if no recent data exists
        asyncio.create_task(run_initial_collection())
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

async def run_initial_collection():
    """Run initial data collection on startup"""
    try:
        # Wait a bit for the application to fully start
        await asyncio.sleep(30)
        
        # Check if we have recent data
        db = SessionLocal()
        from app.database import Post
        recent_posts = db.query(Post).filter(
            Post.collected_at >= datetime.utcnow() - timedelta(hours=2)
        ).count()
        db.close()
        
        # If no recent data, trigger initial collection
        if recent_posts < 10:
            logger.info("No recent data found, triggering initial collection...")
            await scheduler_instance._collect_reddit_data()
            await asyncio.sleep(60)  # Wait before processing
            await scheduler_instance._process_new_posts()
            await asyncio.sleep(30)  # Wait before trends
            await scheduler_instance._calculate_trends()
        
    except Exception as e:
        logger.error(f"Error in initial collection: {e}")

def stop_scheduler():
    """Stop the background scheduler"""
    scheduler_instance.stop()

def get_scheduler_status():
    """Get scheduler status"""
    return scheduler_instance.get_job_status()

def trigger_job(job_id: str):
    """Trigger a specific job"""
    return scheduler_instance.trigger_job(job_id)