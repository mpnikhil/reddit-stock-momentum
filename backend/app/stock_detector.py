import re
import pandas as pd
import logging
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from app.database import SessionLocal, Stock, StockMention, Post, Comment

logger = logging.getLogger(__name__)

@dataclass
class StockMatch:
    symbol: str
    company_name: str
    confidence: float
    context: str
    position: int

class StockDetector:
    def __init__(self):
        self.stock_symbols: Set[str] = set()
        self.company_names: Dict[str, str] = {}  # symbol -> company_name
        self.excluded_words: Set[str] = {
            # Common false positives
            'A', 'I', 'AM', 'ARE', 'AT', 'BE', 'BY', 'DO', 'FOR', 'FROM', 'HAS', 'HE',
            'IN', 'IS', 'IT', 'OF', 'ON', 'OR', 'TO', 'US', 'WE', 'WHO', 'AND', 'THE',
            'ALL', 'ANY', 'CAN', 'HAD', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY',
            'GET', 'GOT', 'HIM', 'HIS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOW', 'OLD',
            'SEE', 'TWO', 'WAY', 'WHO', 'WHY', 'BOY', 'DID', 'EACH', 'FEW', 'FULL',
            'GOOD', 'HAND', 'HIGH', 'KEEP', 'LAST', 'LEFT', 'LIFE', 'LIVE', 'LONG',
            'MADE', 'MAKE', 'MAN', 'MANY', 'MOST', 'MOVE', 'MUCH', 'MUST', 'NAME',
            'NEED', 'NEXT', 'OPEN', 'OWN', 'PART', 'PLAY', 'RIGHT', 'SAID', 'SAME',
            'SEEM', 'SHOW', 'SIDE', 'TAKE', 'TELL', 'TURN', 'WANT', 'WAYS', 'WELL',
            'WENT', 'WERE', 'WHAT', 'WHEN', 'WHERE', 'WILL', 'WITH', 'WORD', 'WORK',
            'WORLD', 'WOULD', 'WRITE', 'YEAR', 'YEAH', 'YES', 'YET', 'YOU', 'YOUR',
            # Financial/trading terms that aren't stocks
            'DD', 'YOLO', 'HODL', 'FOMO', 'FUD', 'ATH', 'ATL', 'TA', 'FA', 'EOD',
            'AH', 'PM', 'IPO', 'ETF', 'REIT', 'CEO', 'CFO', 'SEC', 'FDA', 'EPA',
            'GDP', 'CPI', 'PPI', 'FOMC', 'FED', 'NYSE', 'NASDAQ', 'DOW', 'SPY',
            'QQQ', 'VIX', 'USD', 'EUR', 'GBP', 'JPY', 'BTC', 'ETH', 'CRYPTO',
            # Common Reddit/internet slang
            'OP', 'TLDR', 'TL;DR', 'IMO', 'IMHO', 'AFAIK', 'FYI', 'PSA', 'AMA',
            'NSFW', 'SFW', 'IRL', 'LOL', 'LMAO', 'SMH', 'TBH', 'NGL', 'FR', 'NO',
            'CAP', 'W', 'L', 'F', 'RIP', 'GG', 'EZ', 'PZ', 'OP', 'OG', 'GOAT'
        }
        self._load_stock_data()
    
    def _load_stock_data(self):
        """Load stock symbols and company names"""
        try:
            # First try to load from database
            db = SessionLocal()
            stocks = db.query(Stock).all()
            
            if stocks:
                for stock in stocks:
                    self.stock_symbols.add(stock.symbol.upper())
                    self.company_names[stock.symbol.upper()] = stock.company_name
                logger.info(f"Loaded {len(self.stock_symbols)} stocks from database")
            else:
                # Load default stock list if database is empty
                self._load_default_stocks()
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error loading stock data: {e}")
            self._load_default_stocks()
    
    def _load_default_stocks(self):
        """Load a default set of popular stocks"""
        default_stocks = {
            # Major tech companies
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'GOOG': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.',
            'META': 'Meta Platforms Inc.',
            'NFLX': 'Netflix Inc.',
            'NVDA': 'NVIDIA Corporation',
            'CRM': 'Salesforce Inc.',
            'ORCL': 'Oracle Corporation',
            'ADBE': 'Adobe Inc.',
            
            # Financial
            'JPM': 'JPMorgan Chase & Co.',
            'BAC': 'Bank of America Corp.',
            'WFC': 'Wells Fargo & Company',
            'GS': 'Goldman Sachs Group Inc.',
            'MS': 'Morgan Stanley',
            'C': 'Citigroup Inc.',
            'V': 'Visa Inc.',
            'MA': 'Mastercard Inc.',
            'PYPL': 'PayPal Holdings Inc.',
            'SQ': 'Block Inc.',
            
            # Other major companies
            'JNJ': 'Johnson & Johnson',
            'PG': 'Procter & Gamble Co.',
            'KO': 'Coca-Cola Company',
            'PEP': 'PepsiCo Inc.',
            'WMT': 'Walmart Inc.',
            'HD': 'Home Depot Inc.',
            'DIS': 'Walt Disney Company',
            'NKE': 'Nike Inc.',
            'MCD': 'McDonalds Corporation',
            'SBUX': 'Starbucks Corporation',
            
            # Popular meme/retail stocks
            'GME': 'GameStop Corp.',
            'AMC': 'AMC Entertainment Holdings Inc.',
            'BB': 'BlackBerry Limited',
            'NOK': 'Nokia Corporation',
            'PLTR': 'Palantir Technologies Inc.',
            'WISH': 'ContextLogic Inc.',
            'CLOV': 'Clover Health Investments Corp.',
            'SOFI': 'SoFi Technologies Inc.',
        }
        
        self.stock_symbols = set(default_stocks.keys())
        self.company_names = default_stocks
        logger.info(f"Loaded {len(default_stocks)} default stocks")
        
        # Save to database
        self._save_stocks_to_db(default_stocks)
    
    def _save_stocks_to_db(self, stocks_dict: Dict[str, str]):
        """Save stock symbols to database"""
        db = SessionLocal()
        try:
            for symbol, company_name in stocks_dict.items():
                existing = db.query(Stock).filter(Stock.symbol == symbol).first()
                if not existing:
                    stock = Stock(symbol=symbol, company_name=company_name)
                    db.add(stock)
            db.commit()
        except Exception as e:
            logger.error(f"Error saving stocks to database: {e}")
            db.rollback()
        finally:
            db.close()
    
    def extract_stock_mentions(self, text: str) -> List[StockMatch]:
        """
        Extract stock mentions from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of StockMatch objects
        """
        if not text:
            return []
        
        matches = []
        text_upper = text.upper()
        
        # Pattern 1: $SYMBOL format (highest confidence)
        dollar_pattern = r'\$([A-Z]{1,5})\b'
        for match in re.finditer(dollar_pattern, text_upper):
            symbol = match.group(1)
            if symbol in self.stock_symbols and symbol not in self.excluded_words:
                context = self._extract_context(text, match.start(), match.end())
                matches.append(StockMatch(
                    symbol=symbol,
                    company_name=self.company_names.get(symbol, symbol),
                    confidence=0.95,
                    context=context,
                    position=match.start()
                ))
        
        # Pattern 2: Standalone stock symbols (medium confidence)
        symbol_pattern = r'\b([A-Z]{2,5})\b'
        for match in re.finditer(symbol_pattern, text_upper):
            symbol = match.group(1)
            if (symbol in self.stock_symbols and 
                symbol not in self.excluded_words and
                not any(m.symbol == symbol for m in matches)):  # Avoid duplicates
                
                # Additional context checking for standalone symbols
                confidence = self._calculate_confidence(text, match, symbol)
                if confidence > 0.3:  # Only include if confidence is reasonable
                    context = self._extract_context(text, match.start(), match.end())
                    matches.append(StockMatch(
                        symbol=symbol,
                        company_name=self.company_names.get(symbol, symbol),
                        confidence=confidence,
                        context=context,
                        position=match.start()
                    ))
        
        # Pattern 3: Company names (lower confidence)
        for symbol, company_name in self.company_names.items():
            if company_name.upper() in text_upper:
                # Skip if we already found this symbol
                if not any(m.symbol == symbol for m in matches):
                    pos = text_upper.find(company_name.upper())
                    context = self._extract_context(text, pos, pos + len(company_name))
                    matches.append(StockMatch(
                        symbol=symbol,
                        company_name=company_name,
                        confidence=0.7,
                        context=context,
                        position=pos
                    ))
        
        # Sort by position and remove overlapping matches
        matches.sort(key=lambda x: x.position)
        return self._remove_overlapping_matches(matches)
    
    def _extract_context(self, text: str, start: int, end: int, 
                        context_length: int = 50) -> str:
        """Extract context around a match"""
        context_start = max(0, start - context_length)
        context_end = min(len(text), end + context_length)
        return text[context_start:context_end].strip()
    
    def _calculate_confidence(self, text: str, match, symbol: str) -> float:
        """Calculate confidence score for a stock symbol match"""
        base_confidence = 0.6
        
        # Check for financial context words nearby
        financial_terms = [
            'stock', 'share', 'price', 'buy', 'sell', 'trading', 'invest',
            'market', 'earnings', 'revenue', 'profit', 'loss', 'gains',
            'portfolio', 'position', 'calls', 'puts', 'options', 'bullish',
            'bearish', 'long', 'short', 'moon', 'rocket', 'diamond', 'hands'
        ]
        
        context_start = max(0, match.start() - 100)
        context_end = min(len(text), match.end() + 100)
        context = text[context_start:context_end].lower()
        
        # Boost confidence if financial terms are nearby
        financial_boost = sum(0.1 for term in financial_terms if term in context)
        base_confidence += min(financial_boost, 0.3)
        
        # Reduce confidence for very short symbols in non-financial context
        if len(symbol) <= 2 and financial_boost == 0:
            base_confidence -= 0.3
        
        return min(base_confidence, 0.9)
    
    def _remove_overlapping_matches(self, matches: List[StockMatch]) -> List[StockMatch]:
        """Remove overlapping matches, keeping the highest confidence"""
        if not matches:
            return []
        
        # Sort by confidence (descending) then position
        matches.sort(key=lambda x: (-x.confidence, x.position))
        
        filtered_matches = []
        used_positions = set()
        
        for match in matches:
            # Check for overlap with existing matches
            overlap = False
            for pos in range(match.position, match.position + len(match.symbol)):
                if pos in used_positions:
                    overlap = True
                    break
            
            if not overlap:
                filtered_matches.append(match)
                for pos in range(match.position, match.position + len(match.symbol)):
                    used_positions.add(pos)
        
        return sorted(filtered_matches, key=lambda x: x.position)
    
    def process_post(self, post_id: str) -> int:
        """
        Process a post to extract and save stock mentions
        
        Returns:
            Number of stock mentions found and saved
        """
        db = SessionLocal()
        try:
            post = db.query(Post).filter(Post.id == post_id).first()
            if not post:
                return 0
            
            # Combine title and content for analysis
            full_text = f"{post.title} {post.content}"
            
            # Extract stock mentions
            matches = self.extract_stock_mentions(full_text)
            
            mentions_saved = 0
            for match in matches:
                # Check if mention already exists
                existing = db.query(StockMention).filter(
                    StockMention.post_id == post_id,
                    StockMention.stock_symbol == match.symbol
                ).first()
                
                if not existing:
                    mention = StockMention(
                        post_id=post_id,
                        stock_symbol=match.symbol,
                        mention_count=1,
                        context_snippet=match.context
                    )
                    db.add(mention)
                    mentions_saved += 1
                else:
                    # Increment mention count if it exists
                    existing.mention_count += 1
            
            db.commit()
            return mentions_saved
            
        except Exception as e:
            logger.error(f"Error processing post {post_id}: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    def process_all_unprocessed_posts(self) -> Dict[str, int]:
        """
        Process all posts that don't have stock mentions yet
        
        Returns:
            Dictionary with processing statistics
        """
        db = SessionLocal()
        stats = {"posts_processed": 0, "mentions_found": 0}
        
        try:
            # Find posts without mentions
            posts_without_mentions = db.query(Post).outerjoin(StockMention).filter(
                StockMention.post_id.is_(None)
            ).all()
            
            for post in posts_without_mentions:
                mentions_count = self.process_post(post.id)
                stats["mentions_found"] += mentions_count
                stats["posts_processed"] += 1
                
                if stats["posts_processed"] % 100 == 0:
                    logger.info(f"Processed {stats['posts_processed']} posts...")
            
            logger.info(f"Processing complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error processing posts: {e}")
            return stats
        finally:
            db.close()
    
    def process_comment(self, comment_id: str) -> int:
        """
        Process a comment to extract and save stock mentions
        
        Returns:
            Number of stock mentions found and saved
        """
        db = SessionLocal()
        try:
            comment = db.query(Comment).filter(Comment.id == comment_id).first()
            if not comment:
                return 0
            
            # Extract stock mentions from comment content
            matches = self.extract_stock_mentions(comment.content)
            
            mentions_saved = 0
            for match in matches:
                # Check if mention already exists
                existing = db.query(StockMention).filter(
                    StockMention.comment_id == comment_id,
                    StockMention.stock_symbol == match.symbol
                ).first()
                
                if not existing:
                    mention = StockMention(
                        comment_id=comment_id,
                        stock_symbol=match.symbol,
                        mention_count=1,
                        context_snippet=match.context,
                        source_type="comment"
                    )
                    db.add(mention)
                    mentions_saved += 1
                else:
                    # Increment mention count if it exists
                    existing.mention_count += 1
            
            db.commit()
            return mentions_saved
            
        except Exception as e:
            logger.error(f"Error processing comment {comment_id}: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    def process_all_unprocessed_comments(self) -> Dict[str, int]:
        """
        Process all comments that don't have stock mentions yet
        
        Returns:
            Dictionary with processing statistics
        """
        db = SessionLocal()
        stats = {"comments_processed": 0, "mentions_found": 0}
        
        try:
            # Find comments without mentions
            comments_without_mentions = db.query(Comment).outerjoin(
                StockMention, StockMention.comment_id == Comment.id
            ).filter(
                StockMention.comment_id.is_(None)
            ).all()
            
            for comment in comments_without_mentions:
                mentions_count = self.process_comment(comment.id)
                stats["mentions_found"] += mentions_count
                stats["comments_processed"] += 1
                
                if stats["comments_processed"] % 100 == 0:
                    logger.info(f"Processed {stats['comments_processed']} comments...")
            
            logger.info(f"Comment processing complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error processing comments: {e}")
            return stats
        finally:
            db.close()

# Global stock detector instance
stock_detector = StockDetector()