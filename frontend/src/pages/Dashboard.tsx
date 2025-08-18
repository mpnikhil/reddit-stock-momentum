import React, { useState } from 'react';
import { MessageSquare, TrendingUp, Users, Activity, Zap } from 'lucide-react';
import { usePolling } from '../hooks/useApi';
import { apiClient, formatNumber } from '../utils/api';
import { TimeRange } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import StatCard from '../components/StatCard';
import TrendingStockCard from '../components/TrendingStockCard';
import TimeRangeSelector, { timeRangeToDays } from '../components/TimeRangeSelector';

export default function Dashboard() {
  const [timeRange, setTimeRange] = useState<TimeRange>('1d');
  const [minMentions, setMinMentions] = useState(5);

  // Fetch trending stocks with polling
  const { data: trendingData, loading: trendingLoading, error: trendingError, refetch: refetchTrending } = usePolling(
    () => apiClient.getTrendingStocks(timeRangeToDays(timeRange), 20, minMentions),
    30000, // Poll every 30 seconds
    [timeRange, minMentions]
  );

  // Fetch system stats
  const { data: statsData, loading: statsLoading, error: statsError } = usePolling(
    () => apiClient.getSystemStats(),
    60000 // Poll every minute
  );

  // Fetch momentum spikes
  const { data: spikesData, loading: spikesLoading } = usePolling(
    () => apiClient.getMomentumSpikes(50),
    60000
  );

  if (statsLoading && trendingLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Stock Momentum Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Track trending stocks and sentiment across Reddit communities
        </p>
      </div>

      {/* System Stats */}
      {statsError ? (
        <ErrorMessage error={statsError} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Posts"
            value={formatNumber(statsData?.total_posts || 0)}
            subtitle="All time"
            icon={MessageSquare}
            color="primary"
          />
          <StatCard
            title="Active Stocks"
            value={formatNumber(statsData?.total_stocks || 0)}
            subtitle="Being tracked"
            icon={TrendingUp}
            color="success"
          />
          <StatCard
            title="Stock Mentions"
            value={formatNumber(statsData?.total_mentions || 0)}
            subtitle="All time"
            icon={Users}
            color="warning"
          />
          <StatCard
            title="Recent Activity"
            value={formatNumber(statsData?.recent_24h?.posts || 0)}
            subtitle="Posts in 24h"
            icon={Activity}
            color="danger"
          />
        </div>
      )}

      {/* Momentum Spikes Alert */}
      {spikesData && spikesData.momentum_spikes.length > 0 && (
        <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
          <div className="flex items-center">
            <Zap className="h-5 w-5 text-warning-600" />
            <h3 className="ml-2 text-sm font-medium text-warning-800">
              Momentum Spikes Detected ({spikesData.momentum_spikes.length})
            </h3>
          </div>
          <div className="mt-2 text-sm text-warning-700">
            {spikesData.momentum_spikes.slice(0, 3).map((spike, index) => (
              <span key={spike.symbol}>
                <strong>{spike.symbol}</strong> (+{spike.momentum_score.toFixed(1)}%)
                {index < Math.min(2, spikesData.momentum_spikes.length - 1) && ', '}
              </span>
            ))}
            {spikesData.momentum_spikes.length > 3 && '...'}
          </div>
        </div>
      )}

      {/* Trending Stocks Section */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Trending Stocks</h2>
          
          <div className="mt-4 sm:mt-0 flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Min mentions:</label>
              <select
                value={minMentions}
                onChange={(e) => setMinMentions(Number(e.target.value))}
                className="px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value={3}>3+</option>
                <option value={5}>5+</option>
                <option value={10}>10+</option>
                <option value={20}>20+</option>
              </select>
            </div>
            
            <TimeRangeSelector
              value={timeRange}
              onChange={setTimeRange}
            />
          </div>
        </div>

        {trendingError ? (
          <ErrorMessage error={trendingError} onRetry={refetchTrending} />
        ) : trendingLoading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : trendingData && trendingData.trending_stocks.length > 0 ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {trendingData.trending_stocks.map((stock, index) => (
                <TrendingStockCard
                  key={stock.symbol}
                  stock={stock}
                  rank={index + 1}
                />
              ))}
            </div>
            
            <div className="mt-6 text-center text-sm text-gray-500">
              Showing {trendingData.trending_stocks.length} of {trendingData.total_count} trending stocks
              {trendingData.period_days > 1 && ` over ${trendingData.period_days} days`}
            </div>
          </>
        ) : (
          <div className="text-center py-12">
            <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No trending stocks found</h3>
            <p className="text-gray-600">
              Try adjusting the time range or minimum mentions filter.
            </p>
          </div>
        )}
      </div>

      {/* Top Subreddits */}
      {statsData?.top_subreddits_24h && statsData.top_subreddits_24h.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Most Active Subreddits (24h)</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {statsData.top_subreddits_24h.map((subreddit) => (
              <div key={subreddit.subreddit} className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">r/{subreddit.subreddit}</h3>
                    <p className="text-sm text-gray-600">{subreddit.posts} posts</p>
                  </div>
                  <div className="h-8 w-8 bg-primary-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-bold text-primary-700">
                      {subreddit.posts}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}