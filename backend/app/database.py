from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database setup
DATABASE_URL = "sqlite:///./data/reddit_stocks.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Post(Base):
    __tablename__ = "posts"
    
    id = Column(String, primary_key=True)  # Reddit post ID
    title = Column(String, nullable=False)
    content = Column(Text)
    author = Column(String)
    subreddit = Column(String, nullable=False)
    created_time = Column(DateTime, nullable=False)
    score = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    url = Column(String)
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    mentions = relationship("StockMention", back_populates="post")
    comments = relationship("Comment", backref="post")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_posts_subreddit_created', 'subreddit', 'created_time'),
        Index('idx_posts_created_time', 'created_time'),
    )

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(String, primary_key=True)  # Reddit comment ID
    post_id = Column(String, ForeignKey("posts.id"), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String)
    score = Column(Integer, default=0)  # Upvotes - downvotes
    created_time = Column(DateTime, nullable=False)
    parent_id = Column(String)  # Parent comment ID for threading
    depth = Column(Integer, default=0)  # Comment depth (0 = top-level)
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_comments_post_score', 'post_id', 'score'),
        Index('idx_comments_created_time', 'created_time'),
    )

class Stock(Base):
    __tablename__ = "stocks"
    
    symbol = Column(String, primary_key=True)
    company_name = Column(String)
    market_cap = Column(Float)
    sector = Column(String)
    last_price = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to mentions and trends
    mentions = relationship("StockMention", back_populates="stock")
    trends = relationship("DailyTrend", back_populates="stock")

class StockMention(Base):
    __tablename__ = "stock_mentions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String, ForeignKey("posts.id"), nullable=True)
    comment_id = Column(String, ForeignKey("comments.id"), nullable=True)
    stock_symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    mention_count = Column(Integer, default=1)
    sentiment_score = Column(Float)  # -1 to 1 sentiment score
    context_snippet = Column(Text)  # Text around the mention
    source_type = Column(String, default="post")  # "post" or "comment"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("Post", back_populates="mentions")
    comment = relationship("Comment", backref="mentions")
    stock = relationship("Stock", back_populates="mentions")
    
    # Indexes
    __table_args__ = (
        Index('idx_mentions_stock_created', 'stock_symbol', 'created_at'),
        Index('idx_mentions_post_stock', 'post_id', 'stock_symbol'),
        Index('idx_mentions_comment_stock', 'comment_id', 'stock_symbol'),
    )

class DailyTrend(Base):
    __tablename__ = "daily_trends"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    stock_symbol = Column(String, ForeignKey("stocks.symbol"), nullable=False)
    mention_count = Column(Integer, default=0)
    unique_posts = Column(Integer, default=0)
    avg_sentiment = Column(Float)
    momentum_score = Column(Float)  # Calculated momentum based on changes
    volume_spike = Column(Float)  # Percentage change from average
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    stock = relationship("Stock", back_populates="trends")
    
    # Indexes
    __table_args__ = (
        Index('idx_trends_date_stock', 'date', 'stock_symbol'),
        Index('idx_trends_momentum', 'momentum_score'),
    )

class Subreddit(Base):
    __tablename__ = "subreddits"
    
    name = Column(String, primary_key=True)
    display_name = Column(String)
    subscribers = Column(Integer)
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    last_scraped = Column(DateTime)
    posts_collected = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility functions
def init_db():
    """Initialize database with default data"""
    db = SessionLocal()
    
    # Default subreddits to monitor
    default_subreddits = [
        {"name": "stocks", "display_name": "r/stocks"},
        {"name": "investing", "display_name": "r/investing"},
        {"name": "SecurityAnalysis", "display_name": "r/SecurityAnalysis"},
        {"name": "ValueInvesting", "display_name": "r/ValueInvesting"},
        {"name": "StockMarket", "display_name": "r/StockMarket"},
        {"name": "pennystocks", "display_name": "r/pennystocks"},
        {"name": "options", "display_name": "r/options"},
        {"name": "wallstreetbets", "display_name": "r/wallstreetbets"},
        {"name": "financialindependence", "display_name": "r/financialindependence"},
    ]
    
    try:
        for sub_data in default_subreddits:
            existing = db.query(Subreddit).filter(Subreddit.name == sub_data["name"]).first()
            if not existing:
                subreddit = Subreddit(**sub_data)
                db.add(subreddit)
        
        db.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Create all tables
    Base.metadata.create_all(bind=engine)
    # Initialize with default data
    init_db()
    print("Database initialized successfully!")