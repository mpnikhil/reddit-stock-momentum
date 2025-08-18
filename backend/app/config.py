import os
import yaml
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class RedditConfig:
    client_id: str
    client_secret: str
    user_agent: str

@dataclass
class DatabaseConfig:
    url: str
    echo: bool = False

@dataclass
class SchedulerConfig:
    reddit_collection_interval: int = 30
    post_processing_interval: int = 15
    trend_calculation_interval: int = 60

@dataclass
class RateLimitsConfig:
    reddit_requests_per_minute: int = 60
    max_posts_per_subreddit: int = 100

@dataclass
class DataRetentionConfig:
    keep_posts_days: int = 90
    keep_trends_days: int = 365

@dataclass
class AppConfig:
    database: DatabaseConfig
    scheduler: SchedulerConfig
    rate_limits: RateLimitsConfig
    data_retention: DataRetentionConfig

@dataclass
class SubredditConfig:
    default_active: List[str]
    additional: List[str] = None

@dataclass
class StockDetectionConfig:
    min_mentions_for_trend: int = 3
    confidence_threshold: float = 0.3
    excluded_symbols: List[str] = None

@dataclass
class SentimentConfig:
    update_batch_size: int = 200
    confidence_threshold: float = 0.5

@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "logs/app.log"
    max_file_size: str = "10MB"
    backup_count: int = 5

@dataclass
class Config:
    reddit: RedditConfig
    app: AppConfig
    subreddits: SubredditConfig
    stock_detection: StockDetectionConfig
    sentiment: SentimentConfig
    logging: LoggingConfig

class ConfigManager:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self._config: Optional[Config] = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file or environment variables"""
        try:
            config_data = self._load_from_file()
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found. Using environment variables and defaults.")
            config_data = self._load_from_env()
        
        self._config = self._parse_config(config_data)
        self._setup_logging()
    
    def _load_from_file(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables with defaults"""
        return {
            'reddit': {
                'client_id': os.getenv('REDDIT_CLIENT_ID'),
                'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
                'user_agent': os.getenv('REDDIT_USER_AGENT', 'StockMomentumMonitor/1.0')
            },
            'app': {
                'database': {
                    'url': os.getenv('DATABASE_URL', 'sqlite:///./data/reddit_stocks.db'),
                    'echo': os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
                },
                'scheduler': {
                    'reddit_collection_interval': int(os.getenv('REDDIT_COLLECTION_INTERVAL', '30')),
                    'post_processing_interval': int(os.getenv('POST_PROCESSING_INTERVAL', '15')),
                    'trend_calculation_interval': int(os.getenv('TREND_CALCULATION_INTERVAL', '60'))
                },
                'rate_limits': {
                    'reddit_requests_per_minute': int(os.getenv('REDDIT_REQUESTS_PER_MINUTE', '60')),
                    'max_posts_per_subreddit': int(os.getenv('MAX_POSTS_PER_SUBREDDIT', '100'))
                },
                'data_retention': {
                    'keep_posts_days': int(os.getenv('KEEP_POSTS_DAYS', '90')),
                    'keep_trends_days': int(os.getenv('KEEP_TRENDS_DAYS', '365'))
                }
            },
            'subreddits': {
                'default_active': [
                    'stocks', 'investing', 'SecurityAnalysis', 'ValueInvesting',
                    'StockMarket', 'pennystocks', 'options', 'wallstreetbets',
                    'financialindependence'
                ],
                'additional': []
            },
            'stock_detection': {
                'min_mentions_for_trend': int(os.getenv('MIN_MENTIONS_FOR_TREND', '3')),
                'confidence_threshold': float(os.getenv('CONFIDENCE_THRESHOLD', '0.3')),
                'excluded_symbols': [
                    'US', 'IT', 'AM', 'PM', 'CEO', 'CFO', 'SEC', 'FDA', 'EPA'
                ]
            },
            'sentiment': {
                'update_batch_size': int(os.getenv('SENTIMENT_BATCH_SIZE', '200')),
                'confidence_threshold': float(os.getenv('SENTIMENT_CONFIDENCE', '0.5'))
            },
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'file': os.getenv('LOG_FILE', 'logs/app.log'),
                'max_file_size': os.getenv('LOG_MAX_SIZE', '10MB'),
                'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5'))
            }
        }
    
    def _parse_config(self, config_data: Dict[str, Any]) -> Config:
        """Parse configuration data into structured config objects"""
        try:
            # Reddit config
            reddit_data = config_data.get('reddit', {})
            reddit_config = RedditConfig(
                client_id=reddit_data.get('client_id'),
                client_secret=reddit_data.get('client_secret'),
                user_agent=reddit_data.get('user_agent', 'StockMomentumMonitor/1.0')
            )
            
            # App config
            app_data = config_data.get('app', {})
            
            db_data = app_data.get('database', {})
            database_config = DatabaseConfig(
                url=db_data.get('url', 'sqlite:///./data/reddit_stocks.db'),
                echo=db_data.get('echo', False)
            )
            
            scheduler_data = app_data.get('scheduler', {})
            scheduler_config = SchedulerConfig(
                reddit_collection_interval=scheduler_data.get('reddit_collection_interval', 30),
                post_processing_interval=scheduler_data.get('post_processing_interval', 15),
                trend_calculation_interval=scheduler_data.get('trend_calculation_interval', 60)
            )
            
            rate_limits_data = app_data.get('rate_limits', {})
            rate_limits_config = RateLimitsConfig(
                reddit_requests_per_minute=rate_limits_data.get('reddit_requests_per_minute', 60),
                max_posts_per_subreddit=rate_limits_data.get('max_posts_per_subreddit', 100)
            )
            
            retention_data = app_data.get('data_retention', {})
            retention_config = DataRetentionConfig(
                keep_posts_days=retention_data.get('keep_posts_days', 90),
                keep_trends_days=retention_data.get('keep_trends_days', 365)
            )
            
            app_config = AppConfig(
                database=database_config,
                scheduler=scheduler_config,
                rate_limits=rate_limits_config,
                data_retention=retention_config
            )
            
            # Subreddit config
            subreddit_data = config_data.get('subreddits', {})
            subreddit_config = SubredditConfig(
                default_active=subreddit_data.get('default_active', []),
                additional=subreddit_data.get('additional', [])
            )
            
            # Stock detection config
            stock_detection_data = config_data.get('stock_detection', {})
            stock_detection_config = StockDetectionConfig(
                min_mentions_for_trend=stock_detection_data.get('min_mentions_for_trend', 3),
                confidence_threshold=stock_detection_data.get('confidence_threshold', 0.3),
                excluded_symbols=stock_detection_data.get('excluded_symbols', [])
            )
            
            # Sentiment config
            sentiment_data = config_data.get('sentiment', {})
            sentiment_config = SentimentConfig(
                update_batch_size=sentiment_data.get('update_batch_size', 200),
                confidence_threshold=sentiment_data.get('confidence_threshold', 0.5)
            )
            
            # Logging config
            logging_data = config_data.get('logging', {})
            logging_config = LoggingConfig(
                level=logging_data.get('level', 'INFO'),
                file=logging_data.get('file', 'logs/app.log'),
                max_file_size=logging_data.get('max_file_size', '10MB'),
                backup_count=logging_data.get('backup_count', 5)
            )
            
            return Config(
                reddit=reddit_config,
                app=app_config,
                subreddits=subreddit_config,
                stock_detection=stock_detection_config,
                sentiment=sentiment_config,
                logging=logging_config
            )
            
        except Exception as e:
            logger.error(f"Error parsing configuration: {e}")
            raise ValueError(f"Invalid configuration: {e}")
    
    def _setup_logging(self):
        """Setup logging based on configuration"""
        try:
            # Create logs directory if it doesn't exist
            log_file = Path(self._config.logging.file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Configure logging
            logging.basicConfig(
                level=getattr(logging, self._config.logging.level.upper()),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
            
        except Exception as e:
            print(f"Warning: Could not setup logging: {e}")
    
    @property
    def config(self) -> Config:
        """Get the loaded configuration"""
        if self._config is None:
            raise RuntimeError("Configuration not loaded")
        return self._config
    
    def validate_reddit_config(self) -> bool:
        """Validate that Reddit API credentials are configured"""
        reddit_config = self._config.reddit
        return (reddit_config.client_id is not None and 
                reddit_config.client_secret is not None and
                reddit_config.client_id != "your_client_id_here" and
                reddit_config.client_secret != "your_client_secret_here")
    
    def get_reddit_credentials(self) -> Dict[str, str]:
        """Get Reddit API credentials"""
        reddit_config = self._config.reddit
        return {
            'client_id': reddit_config.client_id,
            'client_secret': reddit_config.client_secret,
            'user_agent': reddit_config.user_agent
        }

# Global config manager instance
config_manager = ConfigManager()

def get_config() -> Config:
    """Get the global configuration"""
    return config_manager.config

def validate_config() -> bool:
    """Validate that all required configuration is present"""
    return config_manager.validate_reddit_config()