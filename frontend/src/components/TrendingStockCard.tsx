import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, TrendingDown, MessageSquare, Users } from 'lucide-react';
import { TrendingStock } from '../types';
import { formatNumber, formatPercent, getSentimentColor, getMomentumColor } from '../utils/api';

interface TrendingStockCardProps {
  stock: TrendingStock;
  rank?: number;
}

export default function TrendingStockCard({ stock, rank }: TrendingStockCardProps) {
  const sentimentColor = getSentimentColor(stock.avg_sentiment);
  const momentumColor = getMomentumColor(stock.momentum_score);
  
  const MomentumIcon = stock.momentum_score > 0 ? TrendingUp : TrendingDown;

  return (
    <Link to={`/stock/${stock.symbol}`}>
      <div className="stat-card group">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              {rank && (
                <span className="inline-flex items-center justify-center w-6 h-6 bg-primary-100 text-primary-700 text-xs font-bold rounded-full">
                  {rank}
                </span>
              )}
              <h3 className="text-lg font-bold text-gray-900 group-hover:text-primary-600 transition-colors">
                {stock.symbol}
              </h3>
              <MomentumIcon className={`h-4 w-4 ${momentumColor}`} />
            </div>
            
            <p className="text-sm text-gray-600 mb-3 line-clamp-1">
              {stock.company_name}
            </p>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-2">
                <MessageSquare className="h-4 w-4 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Mentions</p>
                  <p className="font-semibold text-gray-900">
                    {formatNumber(stock.total_mentions)}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Users className="h-4 w-4 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Posts</p>
                  <p className="font-semibold text-gray-900">
                    {formatNumber(stock.total_posts)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="text-right">
            <div className="mb-2">
              <p className="text-xs text-gray-500">Momentum</p>
              <p className={`font-bold ${momentumColor}`}>
                {stock.momentum_score > 0 ? '+' : ''}{formatPercent(stock.momentum_score)}
              </p>
            </div>
            
            <div>
              <p className="text-xs text-gray-500">Sentiment</p>
              <p className={`font-semibold ${sentimentColor}`}>
                {stock.avg_sentiment > 0.1 ? 'Positive' : 
                 stock.avg_sentiment < -0.1 ? 'Negative' : 'Neutral'}
              </p>
            </div>
          </div>
        </div>

        {stock.volume_spike > 20 && (
          <div className="mt-3 px-2 py-1 bg-warning-50 border border-warning-200 rounded text-xs">
            <span className="text-warning-700 font-medium">
              🔥 Volume spike: +{formatPercent(stock.volume_spike)}
            </span>
          </div>
        )}
      </div>
    </Link>
  );
}