import { 
  TrendingStock, 
  StockDetails, 
  StockMention, 
  MomentumSpike, 
  Subreddit, 
  SystemStats, 
  SchedulerStatus,
  SearchResult 
} from '../types';

const API_BASE = '/api';

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  // Trending stocks
  async getTrendingStocks(days = 1, limit = 20, minMentions = 5): Promise<{
    trending_stocks: TrendingStock[];
    total_count: number;
    period_days: number;
    generated_at: string;
  }> {
    return this.request(`/trending?days=${days}&limit=${limit}&min_mentions=${minMentions}`);
  }

  // Stock details
  async getStockDetails(symbol: string, days = 7): Promise<StockDetails> {
    return this.request(`/stocks/${symbol}?days=${days}`);
  }

  // Stock mentions
  async getStockMentions(symbol: string, days = 7, limit = 50): Promise<{
    symbol: string;
    mentions: StockMention[];
    total_mentions: number;
    period_days: number;
  }> {
    return this.request(`/stocks/${symbol}/mentions?days=${days}&limit=${limit}`);
  }

  // Momentum spikes
  async getMomentumSpikes(threshold = 50.0): Promise<{
    momentum_spikes: MomentumSpike[];
    threshold: number;
    total_spikes: number;
    generated_at: string;
  }> {
    return this.request(`/momentum-spikes?threshold=${threshold}`);
  }

  // Subreddits
  async getSubreddits(): Promise<{
    subreddits: Subreddit[];
    total_subreddits: number;
    active_subreddits: number;
  }> {
    return this.request('/subreddits');
  }

  // Search stocks
  async searchStocks(query: string, limit = 10): Promise<{
    query: string;
    results: SearchResult[];
    total_results: number;
  }> {
    return this.request(`/search?query=${encodeURIComponent(query)}&limit=${limit}`);
  }

  // Sentiment summary
  async getSentimentSummary(days = 7, limit = 20): Promise<{
    sentiment_summary: Array<{
      symbol: string;
      company_name: string;
      mention_count: number;
      avg_sentiment: number;
      min_sentiment: number;
      max_sentiment: number;
      sentiment_label: string;
    }>;
    period_days: number;
    total_stocks: number;
    generated_at: string;
  }> {
    return this.request(`/sentiment-summary?days=${days}&limit=${limit}`);
  }

  // System stats
  async getSystemStats(): Promise<SystemStats> {
    return this.request('/stats');
  }

  // Scheduler status
  async getSchedulerStatus(): Promise<SchedulerStatus> {
    return this.request('/scheduler/status');
  }

  // Trigger scheduler job
  async triggerSchedulerJob(jobId: string): Promise<{ message: string }> {
    return this.request(`/scheduler/trigger/${jobId}`, { method: 'POST' });
  }

  // Export trending data
  async exportTrendingData(days = 7, format: 'json' | 'csv' = 'json'): Promise<any> {
    if (format === 'csv') {
      const response = await fetch(`${API_BASE}/export/trending?days=${days}&format=csv`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.blob();
    }
    
    return this.request(`/export/trending?days=${days}&format=json`);
  }
}

export const apiClient = new ApiClient();

// Utility functions for data formatting
export const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
};

export const formatPercent = (num: number): string => {
  return `${num.toFixed(1)}%`;
};

export const formatSentiment = (sentiment: number): string => {
  if (sentiment > 0.1) return 'Positive';
  if (sentiment < -0.1) return 'Negative';
  return 'Neutral';
};

export const getSentimentColor = (sentiment: number): string => {
  if (sentiment > 0.1) return 'text-success-600';
  if (sentiment < -0.1) return 'text-danger-600';
  return 'text-gray-600';
};

export const getMomentumColor = (momentum: number): string => {
  if (momentum > 20) return 'text-success-600';
  if (momentum < -20) return 'text-danger-600';
  return 'text-gray-600';
};

export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = diffMs / (1000 * 60 * 60);
  const diffDays = diffHours / 24;

  if (diffHours < 1) {
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    return `${diffMinutes}m ago`;
  }
  if (diffHours < 24) {
    return `${Math.floor(diffHours)}h ago`;
  }
  if (diffDays < 7) {
    return `${Math.floor(diffDays)}d ago`;
  }
  
  return formatDate(dateString);
};