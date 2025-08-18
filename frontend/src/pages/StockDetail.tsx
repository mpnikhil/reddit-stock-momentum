import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, ExternalLink, MessageSquare, TrendingUp, Calendar } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { apiClient, formatNumber, formatRelativeTime, getSentimentColor } from '../utils/api';
import { TimeRange } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import TrendChart from '../components/TrendChart';
import SentimentChart from '../components/SentimentChart';
import TimeRangeSelector, { timeRangeToDays } from '../components/TimeRangeSelector';

export default function StockDetail() {
  const { symbol } = useParams<{ symbol: string }>();
  const [timeRange, setTimeRange] = useState<TimeRange>('7d');

  const { data: stockData, loading, error, refetch } = useApi(
    () => apiClient.getStockDetails(symbol!, timeRangeToDays(timeRange)),
    [symbol, timeRange]
  );

  const { data: mentionsData, loading: mentionsLoading } = useApi(
    () => apiClient.getStockMentions(symbol!, timeRangeToDays(timeRange), 20),
    [symbol, timeRange]
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <Link to="/" className="inline-flex items-center text-primary-600 hover:text-primary-700">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Link>
        <ErrorMessage error={error} onRetry={refetch} />
      </div>
    );
  }

  if (!stockData) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link to="/" className="inline-flex items-center text-primary-600 hover:text-primary-700 mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Link>
        
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{stockData.symbol}</h1>
            <p className="text-lg text-gray-600 mt-1">{stockData.company_name}</p>
            {stockData.sector && (
              <p className="text-sm text-gray-500 mt-1">Sector: {stockData.sector}</p>
            )}
          </div>
          
          <div className="mt-4 sm:mt-0">
            <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
          </div>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card text-center">
          <MessageSquare className="h-8 w-8 text-primary-600 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">
            {formatNumber(stockData.sentiment_summary.total_mentions)}
          </div>
          <div className="text-sm text-gray-500">Total Mentions</div>
        </div>
        
        <div className="card text-center">
          <TrendingUp className="h-8 w-8 text-success-600 mx-auto mb-2" />
          <div className={`text-2xl font-bold ${getSentimentColor(stockData.sentiment_summary.average_sentiment)}`}>
            {stockData.sentiment_summary.average_sentiment > 0.1 ? 'Positive' :
             stockData.sentiment_summary.average_sentiment < -0.1 ? 'Negative' : 'Neutral'}
          </div>
          <div className="text-sm text-gray-500">Avg Sentiment</div>
        </div>
        
        <div className="card text-center">
          <Calendar className="h-8 w-8 text-warning-600 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">
            {stockData.trend_history.length}
          </div>
          <div className="text-sm text-gray-500">Days of Data</div>
        </div>
        
        <div className="card text-center">
          <div className="h-8 w-8 bg-danger-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <span className="text-danger-600 font-bold">%</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {stockData.trend_history.length > 0 ? 
              `${stockData.trend_history[stockData.trend_history.length - 1]?.momentum_score.toFixed(1)}%` : 
              'N/A'
            }
          </div>
          <div className="text-sm text-gray-500">Latest Momentum</div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TrendChart
          data={stockData.trend_history}
          title="Mention Trends"
          type="mentions"
        />
        
        <SentimentChart sentimentData={stockData.sentiment_summary} />
        
        <TrendChart
          data={stockData.trend_history}
          title="Sentiment Over Time"
          type="sentiment"
        />
        
        <TrendChart
          data={stockData.trend_history}
          title="Momentum Score"
          type="momentum"
        />
      </div>

      {/* Recent Posts */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Recent Posts</h2>
        
        {stockData.recent_posts.length > 0 ? (
          <div className="space-y-4">
            {stockData.recent_posts.map((post) => (
              <div key={post.id} className="card hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900 mb-2 line-clamp-2">
                      {post.title}
                    </h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>r/{post.subreddit}</span>
                      <span>{formatRelativeTime(post.created_time)}</span>
                      <span>Score: {post.score}</span>
                      {post.sentiment_score !== null && (
                        <span className={getSentimentColor(post.sentiment_score)}>
                          Sentiment: {post.sentiment_score.toFixed(2)}
                        </span>
                      )}
                    </div>
                  </div>
                  <ExternalLink className="h-4 w-4 text-gray-400 ml-4 flex-shrink-0" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No recent posts</h3>
            <p className="text-gray-600">
              No posts found for {stockData.symbol} in the selected time range.
            </p>
          </div>
        )}
      </div>

      {/* Detailed Mentions */}
      {mentionsData && mentionsData.mentions.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Recent Mentions</h2>
          
          {mentionsLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="space-y-4">
              {mentionsData.mentions.slice(0, 10).map((mention) => (
                <div key={mention.mention_id} className="card">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-medium text-gray-900 line-clamp-1">
                      {mention.post_title}
                    </h3>
                    <span className="text-xs text-gray-500 ml-4 flex-shrink-0">
                      {formatRelativeTime(mention.created_time)}
                    </span>
                  </div>
                  
                  {mention.context_snippet && (
                    <p className="text-sm text-gray-600 mb-3 italic">
                      "{mention.context_snippet}"
                    </p>
                  )}
                  
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-4 text-gray-500">
                      <span>r/{mention.subreddit}</span>
                      <span>Mentions: {mention.mention_count}</span>
                      <span>Score: {mention.post_score}</span>
                    </div>
                    
                    {mention.sentiment_score !== null && (
                      <span className={`font-medium ${getSentimentColor(mention.sentiment_score)}`}>
                        {mention.sentiment_score > 0.1 ? 'Positive' :
                         mention.sentiment_score < -0.1 ? 'Negative' : 'Neutral'}
                      </span>
                    )}
                  </div>
                </div>
              ))}
              
              {mentionsData.mentions.length > 10 && (
                <div className="text-center text-sm text-gray-500">
                  Showing 10 of {mentionsData.total_mentions} mentions
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}