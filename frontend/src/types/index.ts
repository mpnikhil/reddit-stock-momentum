export interface TrendingStock {
  symbol: string;
  company_name: string;
  total_mentions: number;
  total_posts: number;
  avg_sentiment: number;
  momentum_score: number;
  volume_spike: number;
  latest_date: string;
}

export interface StockDetails {
  symbol: string;
  company_name: string;
  market_cap?: number;
  sector?: string;
  trend_history: TrendDataPoint[];
  sentiment_summary: SentimentSummary;
  recent_posts: RecentPost[];
  data_period_days: number;
}

export interface TrendDataPoint {
  date: string;
  mention_count: number;
  unique_posts: number;
  avg_sentiment: number;
  momentum_score: number;
  volume_spike: number;
}

export interface SentimentSummary {
  symbol: string;
  period_days: number;
  total_mentions: number;
  average_sentiment: number;
  positive_mentions: number;
  negative_mentions: number;
  neutral_mentions: number;
  max_sentiment: number;
  min_sentiment: number;
}

export interface RecentPost {
  id: string;
  title: string;
  subreddit: string;
  created_time: string;
  score: number;
  sentiment_score?: number;
}

export interface StockMention {
  mention_id: number;
  post_id: string;
  post_title: string;
  subreddit: string;
  mention_count: number;
  sentiment_score?: number;
  context_snippet?: string;
  created_time: string;
  post_score: number;
  post_url: string;
}

export interface MomentumSpike {
  symbol: string;
  company_name: string;
  momentum_score: number;
  volume_spike: number;
  mention_count: number;
  avg_sentiment: number;
  date: string;
}

export interface Subreddit {
  name: string;
  display_name: string;
  is_active: boolean;
  subscribers?: number;
  last_scraped?: string;
  total_posts_collected: number;
  recent_posts_7d: number;
}

export interface SystemStats {
  total_posts: number;
  total_stocks: number;
  total_mentions: number;
  recent_24h: {
    posts: number;
    mentions: number;
  };
  top_subreddits_24h: Array<{
    subreddit: string;
    posts: number;
  }>;
  reddit_api_status: {
    remaining?: number;
    reset_timestamp?: number;
    used?: number;
    error?: string;
  };
  generated_at: string;
}

export interface SchedulerJob {
  id: string;
  name: string;
  next_run_time?: string;
  trigger: string;
  running: boolean;
}

export interface SchedulerStatus {
  scheduler_running: boolean;
  jobs: SchedulerJob[];
  total_jobs: number;
}

export interface SearchResult {
  symbol: string;
  company_name: string;
  market_cap?: number;
  sector?: string;
  recent_mentions_7d: number;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  loading: boolean;
}

export interface FilterOptions {
  days: number;
  minMentions: number;
  sortBy: 'momentum' | 'mentions' | 'sentiment';
  subreddits: string[];
}

export type TimeRange = '1d' | '3d' | '7d' | '30d';

export type SentimentLabel = 'Positive' | 'Negative' | 'Neutral';