import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorMessageProps {
  error: string;
  onRetry?: () => void;
  className?: string;
}

export default function ErrorMessage({ error, onRetry, className = '' }: ErrorMessageProps) {
  return (
    <div className={`bg-danger-50 border border-danger-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-start">
        <AlertCircle className="h-5 w-5 text-danger-600 mt-0.5" />
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-danger-800">Error</h3>
          <p className="mt-1 text-sm text-danger-700">{error}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center px-3 py-1 text-xs font-medium text-danger-700 bg-danger-100 hover:bg-danger-200 rounded-md transition-colors"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Try Again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}