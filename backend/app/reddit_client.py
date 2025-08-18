import praw
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.database import SessionLocal, Post, Subreddit, Comment
import os
import yaml

logger = logging.getLogger(__name__)

class RedditClient:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.reddit = None
        self.config = self._load_config(config_path)
        self._init_reddit_client()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found. Using environment variables.")
            return {
                'reddit': {
                    'client_id': os.getenv('REDDIT_CLIENT_ID'),
                    'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
                    'user_agent': os.getenv('REDDIT_USER_AGENT', 'StockMomentumMonitor/1.0')
                }
            }
    
    def _init_reddit_client(self):
        """Initialize Reddit client with credentials"""
        try:
            reddit_config = self.config.get('reddit', {})
            self.reddit = praw.Reddit(
                client_id=reddit_config.get('client_id'),
                client_secret=reddit_config.get('client_secret'),
                user_agent=reddit_config.get('user_agent', 'StockMomentumMonitor/1.0')
            )
            
            # Test the connection
            self.reddit.auth.limits
            logger.info("Reddit client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            self.reddit = None
    
    def is_connected(self) -> bool:
        """Check if Reddit client is properly connected"""
        return self.reddit is not None
    
    def get_subreddit_posts(self, subreddit_name: str, limit: int = 100, 
                           time_filter: str = 'day') -> List[Dict]:
        """
        Fetch posts from a specific subreddit
        
        Args:
            subreddit_name: Name of the subreddit (without r/)
            limit: Number of posts to fetch
            time_filter: Time filter (hour, day, week, month, year, all)
        
        Returns:
            List of post dictionaries
        """
        if not self.is_connected():
            logger.error("Reddit client not initialized")
            return []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            # Get hot posts
            for post in subreddit.hot(limit=limit//2):
                posts.append(self._extract_post_data(post, subreddit_name))
            
            # Get top posts from the specified time period
            for post in subreddit.top(time_filter=time_filter, limit=limit//2):
                posts.append(self._extract_post_data(post, subreddit_name))
            
            # Remove duplicates based on post ID
            unique_posts = {post['id']: post for post in posts}.values()
            
            logger.info(f"Collected {len(unique_posts)} posts from r/{subreddit_name}")
            return list(unique_posts)
            
        except Exception as e:
            logger.error(f"Error fetching posts from r/{subreddit_name}: {e}")
            return []
    
    def _extract_post_data(self, post, subreddit_name: str) -> Dict:
        """Extract relevant data from a Reddit post"""
        return {
            'id': post.id,
            'title': post.title,
            'content': post.selftext if hasattr(post, 'selftext') else '',
            'author': str(post.author) if post.author else '[deleted]',
            'subreddit': subreddit_name,
            'created_time': datetime.fromtimestamp(post.created_utc),
            'score': post.score,
            'comments_count': post.num_comments,
            'url': post.url,
            'upvote_ratio': getattr(post, 'upvote_ratio', 0.0)
        }
    
    def save_posts_to_db(self, posts: List[Dict]) -> int:
        """
        Save posts to database, avoiding duplicates
        
        Returns:
            Number of new posts saved
        """
        if not posts:
            return 0
        
        db = SessionLocal()
        new_posts_count = 0
        
        try:
            for post_data in posts:
                # Check if post already exists
                existing_post = db.query(Post).filter(Post.id == post_data['id']).first()
                
                if not existing_post:
                    # Create new post
                    post = Post(
                        id=post_data['id'],
                        title=post_data['title'],
                        content=post_data['content'],
                        author=post_data['author'],
                        subreddit=post_data['subreddit'],
                        created_time=post_data['created_time'],
                        score=post_data['score'],
                        comments_count=post_data['comments_count'],
                        url=post_data['url']
                    )
                    db.add(post)
                    new_posts_count += 1
                else:
                    # Update existing post scores (they may have changed)
                    existing_post.score = post_data['score']
                    existing_post.comments_count = post_data['comments_count']
            
            db.commit()
            logger.info(f"Saved {new_posts_count} new posts to database")
            
        except Exception as e:
            logger.error(f"Error saving posts to database: {e}")
            db.rollback()
        finally:
            db.close()
        
        return new_posts_count
    
    def collect_from_all_subreddits(self, limit_per_subreddit: int = 50) -> Dict[str, int]:
        """
        Collect posts from all active subreddits
        
        Returns:
            Dictionary with subreddit names and count of new posts collected
        """
        if not self.is_connected():
            logger.error("Reddit client not initialized")
            return {}
        
        db = SessionLocal()
        results = {}
        
        try:
            # Get all active subreddits
            subreddits = db.query(Subreddit).filter(Subreddit.is_active == 1).all()
            
            for subreddit in subreddits:
                logger.info(f"Collecting posts from r/{subreddit.name}")
                
                # Collect posts
                posts = self.get_subreddit_posts(
                    subreddit.name, 
                    limit=limit_per_subreddit
                )
                
                # Save to database
                new_posts_count = self.save_posts_to_db(posts)
                results[subreddit.name] = new_posts_count
                
                # Update subreddit last_scraped time
                subreddit.last_scraped = datetime.utcnow()
                subreddit.posts_collected += new_posts_count
                
                db.commit()
            
        except Exception as e:
            logger.error(f"Error collecting from subreddits: {e}")
            db.rollback()
        finally:
            db.close()
        
        return results
    
    def get_api_limits(self) -> Dict:
        """Get current API rate limit information"""
        if not self.is_connected():
            return {"error": "Not connected"}
        
        try:
            limits = self.reddit.auth.limits
            return {
                "remaining": limits.get("remaining"),
                "reset_timestamp": limits.get("reset_timestamp"),
                "used": limits.get("used")
            }
        except Exception as e:
            logger.error(f"Error getting API limits: {e}")
            return {"error": str(e)}
    
    def get_post_comments(self, post_id: str, limit: int = 100) -> List[Dict]:
        """
        Fetch comments for a specific post with smart filtering
        
        Args:
            post_id: Reddit post ID
            limit: Maximum number of comments to fetch
            
        Returns:
            List of filtered comment dictionaries
        """
        if not self.is_connected():
            logger.error("Reddit client not initialized")
            return []
        
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=5)  # Expand "more comments" but limit API calls
            
            comments = []
            comment_count = 0
            
            for comment in submission.comments.list():
                if comment_count >= limit:
                    break
                    
                # Apply smart filtering
                if self._should_collect_comment(comment):
                    comment_data = self._extract_comment_data(comment, post_id)
                    comments.append(comment_data)
                    comment_count += 1
            
            logger.info(f"Collected {len(comments)} filtered comments from post {post_id}")
            return comments
            
        except Exception as e:
            logger.error(f"Error fetching comments for post {post_id}: {e}")
            return []
    
    def _should_collect_comment(self, comment) -> bool:
        """
        Smart filtering to determine if a comment should be collected
        
        Args:
            comment: PRAW comment object
            
        Returns:
            Boolean indicating whether to collect this comment
        """
        try:
            # Skip deleted/removed comments
            if comment.author is None or comment.body in ['[deleted]', '[removed]']:
                return False
            
            # Minimum score threshold (upvotes - downvotes)
            if comment.score < 2:
                return False
            
            # Minimum content length (avoid one-word responses)
            if len(comment.body.strip()) < 20:
                return False
            
            # Check for potential stock mentions (quick regex check)
            import re
            stock_pattern = r'\$[A-Z]{1,5}\b|\b[A-Z]{2,5}\b'
            if not re.search(stock_pattern, comment.body.upper()):
                return False
            
            # Skip bot comments
            if hasattr(comment.author, 'name') and any(bot_indicator in comment.author.name.lower() 
                                                     for bot_indicator in ['bot', 'auto', 'moderator']):
                return False
            
            # Limit depth to avoid deep nested conversations
            if hasattr(comment, 'depth') and comment.depth > 3:
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error filtering comment: {e}")
            return False
    
    def _extract_comment_data(self, comment, post_id: str) -> Dict:
        """Extract relevant data from a Reddit comment"""
        try:
            return {
                'id': comment.id,
                'post_id': post_id,
                'content': comment.body,
                'author': str(comment.author) if comment.author else '[deleted]',
                'score': comment.score,
                'created_time': datetime.fromtimestamp(comment.created_utc),
                'parent_id': comment.parent_id if hasattr(comment, 'parent_id') else None,
                'depth': getattr(comment, 'depth', 0)
            }
        except Exception as e:
            logger.error(f"Error extracting comment data: {e}")
            return {}
    
    def save_comments_to_db(self, comments: List[Dict]) -> int:
        """
        Save comments to database, avoiding duplicates
        
        Returns:
            Number of new comments saved
        """
        if not comments:
            return 0
        
        db = SessionLocal()
        new_comments_count = 0
        
        try:
            for comment_data in comments:
                if not comment_data:  # Skip empty comment data
                    continue
                    
                # Check if comment already exists
                existing_comment = db.query(Comment).filter(Comment.id == comment_data['id']).first()
                
                if not existing_comment:
                    # Create new comment
                    comment = Comment(
                        id=comment_data['id'],
                        post_id=comment_data['post_id'],
                        content=comment_data['content'],
                        author=comment_data['author'],
                        score=comment_data['score'],
                        created_time=comment_data['created_time'],
                        parent_id=comment_data.get('parent_id'),
                        depth=comment_data.get('depth', 0)
                    )
                    db.add(comment)
                    new_comments_count += 1
                else:
                    # Update existing comment score (may have changed)
                    existing_comment.score = comment_data['score']
            
            db.commit()
            logger.info(f"Saved {new_comments_count} new comments to database")
            
        except Exception as e:
            logger.error(f"Error saving comments to database: {e}")
            db.rollback()
        finally:
            db.close()
        
        return new_comments_count
    
    def collect_comments_for_recent_posts(self, hours_back: int = 24, max_posts: int = 50) -> Dict[str, int]:
        """
        Collect comments for recent posts that don't have comments yet
        
        Args:
            hours_back: How many hours back to look for posts
            max_posts: Maximum number of posts to process
            
        Returns:
            Dictionary with collection statistics
        """
        if not self.is_connected():
            logger.error("Reddit client not initialized")
            return {}
        
        db = SessionLocal()
        stats = {"posts_processed": 0, "comments_collected": 0}
        
        try:
            # Find recent posts without comments
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            posts_without_comments = db.query(Post).outerjoin(Comment).filter(
                Post.created_time >= cutoff_time,
                Comment.post_id.is_(None),
                Post.comments_count > 5  # Only process posts that likely have comments
            ).limit(max_posts).all()
            
            logger.info(f"Found {len(posts_without_comments)} recent posts to collect comments from")
            
            for post in posts_without_comments:
                try:
                    # Collect comments for this post
                    comments = self.get_post_comments(post.id, limit=50)
                    
                    # Save comments to database
                    new_comments = self.save_comments_to_db(comments)
                    
                    stats["posts_processed"] += 1
                    stats["comments_collected"] += new_comments
                    
                    if stats["posts_processed"] % 10 == 0:
                        logger.info(f"Processed {stats['posts_processed']} posts...")
                        
                except Exception as e:
                    logger.error(f"Error processing comments for post {post.id}: {e}")
                    continue
            
            logger.info(f"Comment collection complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error collecting comments: {e}")
            return stats
        finally:
            db.close()

# Global Reddit client instance
reddit_client = RedditClient()