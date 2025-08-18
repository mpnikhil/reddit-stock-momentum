import React, { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Search as SearchIcon, TrendingUp, MessageSquare } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { apiClient, formatNumber } from '../utils/api';
import { SearchResult } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

export default function Search() {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  // Debounce search query
  const debounce = useCallback((value: string) => {
    const timer = setTimeout(() => {
      setDebouncedQuery(value);
    }, 300);
    
    return () => clearTimeout(timer);
  }, []);

  React.useEffect(() => {
    const cleanup = debounce(query);
    return cleanup;
  }, [query, debounce]);

  const { data: searchData, loading, error } = useApi(
    () => debouncedQuery.length >= 2 ? apiClient.searchStocks(debouncedQuery) : Promise.resolve({ query: '', results: [], total_results: 0 }),
    [debouncedQuery]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Search Stocks</h1>
        <p className="mt-2 text-gray-600">
          Search for stocks by ticker symbol or company name
        </p>
      </div>

      {/* Search Input */}
      <div className="card">
        <div className="relative">
          <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder="Search for stocks (e.g., AAPL, Apple, Tesla)..."
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        
        {query.length > 0 && query.length < 2 && (
          <p className="mt-2 text-sm text-gray-500">
            Type at least 2 characters to search
          </p>
        )}
      </div>

      {/* Search Results */}
      {debouncedQuery.length >= 2 && (
        <div>
          {error ? (
            <ErrorMessage error={error} />
          ) : loading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner size="lg" />
            </div>
          ) : searchData && searchData.results.length > 0 ? (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  Search Results for "{searchData.query}"
                </h2>
                <span className="text-sm text-gray-500">
                  {searchData.total_results} result{searchData.total_results !== 1 ? 's' : ''}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {searchData.results.map((stock) => (
                  <SearchResultCard key={stock.symbol} stock={stock} />
                ))}
              </div>
            </div>
          ) : searchData && searchData.results.length === 0 ? (
            <div className="text-center py-12">
              <SearchIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
              <p className="text-gray-600">
                No stocks found matching "{debouncedQuery}". Try a different search term.
              </p>
            </div>
          ) : null}
        </div>
      )}

      {/* Search Tips */}
      {!debouncedQuery && (
        <div className="card bg-primary-50 border-primary-200">
          <h3 className="text-lg font-medium text-primary-900 mb-3">Search Tips</h3>
          <ul className="space-y-2 text-sm text-primary-800">
            <li>• Search by ticker symbol (e.g., AAPL, TSLA, MSFT)</li>
            <li>• Search by company name (e.g., Apple, Tesla, Microsoft)</li>
            <li>• Partial matches are supported</li>
            <li>• Search is case-insensitive</li>
          </ul>
        </div>
      )}
    </div>
  );
}

interface SearchResultCardProps {
  stock: SearchResult;
}

function SearchResultCard({ stock }: SearchResultCardProps) {
  return (
    <Link to={`/stock/${stock.symbol}`}>
      <div className="stat-card group">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900 group-hover:text-primary-600 transition-colors">
              {stock.symbol}
            </h3>
            <p className="text-sm text-gray-600 line-clamp-2">
              {stock.company_name}
            </p>
          </div>
          <TrendingUp className="h-5 w-5 text-gray-400 group-hover:text-primary-600 transition-colors" />
        </div>

        <div className="space-y-2">
          {stock.sector && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Sector:</span>
              <span className="font-medium text-gray-900">{stock.sector}</span>
            </div>
          )}
          
          {stock.market_cap && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Market Cap:</span>
              <span className="font-medium text-gray-900">
                ${formatNumber(stock.market_cap)}
              </span>
            </div>
          )}
          
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Recent Mentions:</span>
            <div className="flex items-center space-x-1">
              <MessageSquare className="h-3 w-3 text-gray-400" />
              <span className="font-medium text-gray-900">
                {stock.recent_mentions_7d}
              </span>
            </div>
          </div>
        </div>

        {stock.recent_mentions_7d > 10 && (
          <div className="mt-3 px-2 py-1 bg-success-50 border border-success-200 rounded text-xs">
            <span className="text-success-700 font-medium">
              🔥 Popular stock
            </span>
          </div>
        )}
      </div>
    </Link>
  );
}