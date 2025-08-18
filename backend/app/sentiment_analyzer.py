import nltk
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from nltk.sentiment import SentimentIntensityAnalyzer
from app.database import SessionLocal, StockMention, Post
import re

logger = logging.getLogger(__name__)

@dataclass
class SentimentScore:
    compound: float  # Overall sentiment (-1 to 1)
    positive: float  # Positive sentiment (0 to 1)
    negative: float  # Negative sentiment (0 to 1)
    neutral: float   # Neutral sentiment (0 to 1)
    confidence: float  # Confidence in the analysis

class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = None
        self._init_nltk()
        self._init_financial_lexicon()
    
    def _init_nltk(self):
        """Initialize NLTK and download required data"""
        try:
            # Download VADER lexicon if not already present
            nltk.data.find('vader_lexicon')
        except LookupError:
            logger.info("Downloading VADER lexicon...")
            nltk.download('vader_lexicon', quiet=True)
        
        try:
            self.analyzer = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize sentiment analyzer: {e}")
    
    def _init_financial_lexicon(self):
        """Initialize financial-specific sentiment terms"""
        # Financial positive terms
        self.financial_positive = {
            'moon', 'rocket', 'bullish', 'bull', 'pump', 'rally', 'surge', 'spike',
            'breakout', 'breakouts', 'gains', 'profit', 'profits', 'earnings beat',
            'beat expectations', 'strong earnings', 'diamond hands', 'hodl', 'hold',
            'buy the dip', 'btd', 'undervalued', 'oversold', 'recovery', 'bounce',
            'momentum', 'uptrend', 'trending up', 'green', 'bull run', 'bull market',
            'all time high', 'ath', 'new high', 'resistance broken', 'support held',
            'long', 'calls', 'leaps', 'yolo calls', 'to the moon', 'stonks',
            'tendies', 'printing', 'money printer', 'brrrr', 'chad', 'alpha'
        }
        
        # Financial negative terms
        self.financial_negative = {
            'crash', 'bear', 'bearish', 'dump', 'drilling', 'tanking', 'collapse',
            'bloodbath', 'massacre', 'cliff', 'falling knife', 'bagholding', 'bags',
            'paper hands', 'weak hands', 'panic selling', 'sell off', 'selloff',
            'overvalued', 'bubble', 'correction', 'recession', 'depression',
            'downtrend', 'trending down', 'red', 'bear market', 'all time low',
            'atl', 'new low', 'support broken', 'resistance held', 'short',
            'puts', 'shorting', 'squeeze', 'gamma squeeze', 'short squeeze',
            'rug pull', 'pump and dump', 'dead cat bounce', 'trap', 'bull trap',
            'fomo', 'fud', 'fear', 'uncertainty', 'doubt', 'rekt', 'loss porn'
        }
        
        # Update VADER lexicon with financial terms
        if self.analyzer:
            for term in self.financial_positive:
                self.analyzer.lexicon[term] = 2.0
            for term in self.financial_negative:
                self.analyzer.lexicon[term] = -2.0
    
    def analyze_text(self, text: str, context: str = "") -> SentimentScore:
        """
        Analyze sentiment of text with financial context
        
        Args:
            text: Main text to analyze
            context: Additional context (e.g., surrounding text)
            
        Returns:
            SentimentScore object
        """
        if not self.analyzer or not text:
            return SentimentScore(0.0, 0.0, 0.0, 1.0, 0.0)
        
        try:
            # Preprocess text for better financial sentiment analysis
            processed_text = self._preprocess_financial_text(text)
            
            # Get VADER scores
            scores = self.analyzer.polarity_scores(processed_text)
            
            # Calculate confidence based on text length and financial terms
            confidence = self._calculate_confidence(text, context)
            
            # Adjust scores based on financial context
            adjusted_compound = self._adjust_for_financial_context(
                scores['compound'], text, context
            )
            
            return SentimentScore(
                compound=adjusted_compound,
                positive=scores['pos'],
                negative=scores['neg'],
                neutral=scores['neu'],
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return SentimentScore(0.0, 0.0, 0.0, 1.0, 0.0)
    
    def _preprocess_financial_text(self, text: str) -> str:
        """Preprocess text to better handle financial language"""
        # Convert to lowercase
        text = text.lower()
        
        # Handle common financial abbreviations and slang
        replacements = {
            r'\bto the moon\b': 'extremely bullish',
            r'\bdiamond hands?\b': 'very bullish holding',
            r'\bpaper hands?\b': 'weak bearish selling',
            r'\bbuy the dip\b': 'bullish opportunity',
            r'\bhodl\b': 'bullish holding',
            r'\byolo\b': 'risky bullish',
            r'\btendies\b': 'profits gains',
            r'\bbrrr+\b': 'money printing bullish',
            r'\brekt\b': 'big losses',
            r'\bbaghold\w*\b': 'holding losses',
            r'\brug pull\b': 'scam crash',
            r'\bpump and dump\b': 'manipulation crash',
            r'\b🚀+\b': 'rocket bullish',
            r'\b💎\b': 'diamond hands bullish',
            r'\b📈\b': 'chart up bullish',
            r'\b📉\b': 'chart down bearish',
            r'\b🌙\b': 'moon bullish'
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def _adjust_for_financial_context(self, compound: float, text: str, context: str) -> float:
        """Adjust sentiment score based on financial context"""
        adjustment = 0.0
        full_text = f"{text} {context}".lower()
        
        # Look for stock price movements
        price_patterns = [
            (r'\b(?:up|gain|rise|increase)\s+(?:\d+%|\d+\s*percent)', 0.2),
            (r'\b(?:down|loss|drop|decrease|fall)\s+(?:\d+%|\d+\s*percent)', -0.2),
            (r'\b(?:moon|rocket|surge|spike)\b', 0.3),
            (r'\b(?:crash|tank|drill|collapse)\b', -0.3),
            (r'\b(?:buy|long|calls)\b', 0.1),
            (r'\b(?:sell|short|puts)\b', -0.1)
        ]
        
        for pattern, weight in price_patterns:
            if re.search(pattern, full_text):
                adjustment += weight
        
        # Cap the adjustment
        adjustment = max(-0.5, min(0.5, adjustment))
        
        # Apply adjustment
        adjusted = compound + adjustment
        return max(-1.0, min(1.0, adjusted))
    
    def _calculate_confidence(self, text: str, context: str = "") -> float:
        """Calculate confidence in sentiment analysis"""
        base_confidence = 0.5
        
        # Boost confidence for longer texts
        text_length_boost = min(len(text) / 100, 0.3)
        base_confidence += text_length_boost
        
        # Boost confidence if financial terms are present
        full_text = f"{text} {context}".lower()
        financial_term_count = 0
        
        for term in self.financial_positive | self.financial_negative:
            if term in full_text:
                financial_term_count += 1
        
        financial_boost = min(financial_term_count * 0.05, 0.2)
        base_confidence += financial_boost
        
        return min(base_confidence, 0.95)
    
    def analyze_post_sentiment(self, post_id: str) -> Optional[float]:
        """
        Analyze sentiment for a specific post
        
        Returns:
            Compound sentiment score (-1 to 1) or None if analysis fails
        """
        db = SessionLocal()
        try:
            post = db.query(Post).filter(Post.id == post_id).first()
            if not post:
                return None
            
            # Combine title and content
            full_text = f"{post.title} {post.content}"
            
            # Analyze sentiment
            sentiment = self.analyze_text(full_text)
            
            return sentiment.compound
            
        except Exception as e:
            logger.error(f"Error analyzing post sentiment {post_id}: {e}")
            return None
        finally:
            db.close()
    
    def update_mention_sentiments(self, batch_size: int = 100) -> Dict[str, int]:
        """
        Update sentiment scores for stock mentions that don't have them
        
        Returns:
            Dictionary with update statistics
        """
        db = SessionLocal()
        stats = {"updated": 0, "errors": 0}
        
        try:
            # Get mentions without sentiment scores
            mentions = db.query(StockMention).filter(
                StockMention.sentiment_score.is_(None)
            ).limit(batch_size).all()
            
            for mention in mentions:
                try:
                    # Get the associated post
                    post = db.query(Post).filter(Post.id == mention.post_id).first()
                    if not post:
                        continue
                    
                    # Analyze sentiment with context
                    full_text = f"{post.title} {post.content}"
                    sentiment = self.analyze_text(full_text, mention.context_snippet)
                    
                    # Update the mention
                    mention.sentiment_score = sentiment.compound
                    stats["updated"] += 1
                    
                except Exception as e:
                    logger.error(f"Error updating sentiment for mention {mention.id}: {e}")
                    stats["errors"] += 1
            
            db.commit()
            logger.info(f"Updated sentiment for {stats['updated']} mentions")
            
        except Exception as e:
            logger.error(f"Error in batch sentiment update: {e}")
            db.rollback()
        finally:
            db.close()
        
        return stats
    
    def get_stock_sentiment_summary(self, symbol: str, days: int = 7) -> Dict:
        """
        Get sentiment summary for a specific stock over the last N days
        
        Returns:
            Dictionary with sentiment statistics
        """
        db = SessionLocal()
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            mentions = db.query(StockMention).join(Post).filter(
                StockMention.stock_symbol == symbol,
                Post.created_time >= cutoff_date,
                StockMention.sentiment_score.isnot(None)
            ).all()
            
            if not mentions:
                return {"symbol": symbol, "period_days": days, "total_mentions": 0}
            
            sentiments = [m.sentiment_score for m in mentions]
            
            return {
                "symbol": symbol,
                "period_days": days,
                "total_mentions": len(mentions),
                "average_sentiment": sum(sentiments) / len(sentiments),
                "positive_mentions": len([s for s in sentiments if s > 0.1]),
                "negative_mentions": len([s for s in sentiments if s < -0.1]),
                "neutral_mentions": len([s for s in sentiments if -0.1 <= s <= 0.1]),
                "max_sentiment": max(sentiments),
                "min_sentiment": min(sentiments)
            }
            
        except Exception as e:
            logger.error(f"Error getting sentiment summary for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}
        finally:
            db.close()

# Global sentiment analyzer instance
sentiment_analyzer = SentimentAnalyzer()