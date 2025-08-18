import React from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import { SentimentSummary } from '../types';

ChartJS.register(ArcElement, Tooltip, Legend);

interface SentimentChartProps {
  sentimentData: SentimentSummary;
  className?: string;
}

export default function SentimentChart({ sentimentData, className = '' }: SentimentChartProps) {
  if (!sentimentData || sentimentData.total_mentions === 0) {
    return (
      <div className={`card ${className}`}>
        <h3 className="text-lg font-semibold mb-4">Sentiment Distribution</h3>
        <div className="flex items-center justify-center h-64 text-gray-500">
          No sentiment data available
        </div>
      </div>
    );
  }

  const data = {
    labels: ['Positive', 'Neutral', 'Negative'],
    datasets: [
      {
        data: [
          sentimentData.positive_mentions,
          sentimentData.neutral_mentions,
          sentimentData.negative_mentions,
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',  // Green for positive
          'rgba(107, 114, 128, 0.8)', // Gray for neutral
          'rgba(239, 68, 68, 0.8)',   // Red for negative
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(107, 114, 128, 1)',
          'rgba(239, 68, 68, 1)',
        ],
        borderWidth: 2,
      },
    ],
  };

  const options: ChartOptions<'doughnut'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 20,
          usePointStyle: true,
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.label || '';
            const value = context.parsed || 0;
            const percentage = ((value / sentimentData.total_mentions) * 100).toFixed(1);
            return `${label}: ${value} (${percentage}%)`;
          },
        },
      },
    },
    cutout: '60%',
  };

  const averageSentiment = sentimentData.average_sentiment;
  const sentimentLabel = averageSentiment > 0.1 ? 'Positive' : 
                        averageSentiment < -0.1 ? 'Negative' : 'Neutral';
  const sentimentColor = averageSentiment > 0.1 ? 'text-success-600' : 
                        averageSentiment < -0.1 ? 'text-danger-600' : 'text-gray-600';

  return (
    <div className={`card ${className}`}>
      <h3 className="text-lg font-semibold mb-4">Sentiment Distribution</h3>
      
      <div className="relative h-64 mb-4">
        <Doughnut data={data} options={options} />
        
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-2xl font-bold text-gray-900">
            {sentimentData.total_mentions}
          </div>
          <div className="text-sm text-gray-500">Total Mentions</div>
          <div className={`text-sm font-medium ${sentimentColor} mt-1`}>
            {sentimentLabel}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-lg font-bold text-success-600">
            {sentimentData.positive_mentions}
          </div>
          <div className="text-xs text-gray-500">Positive</div>
        </div>
        <div>
          <div className="text-lg font-bold text-gray-600">
            {sentimentData.neutral_mentions}
          </div>
          <div className="text-xs text-gray-500">Neutral</div>
        </div>
        <div>
          <div className="text-lg font-bold text-danger-600">
            {sentimentData.negative_mentions}
          </div>
          <div className="text-xs text-gray-500">Negative</div>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Average Sentiment:</span>
          <span className={`font-medium ${sentimentColor}`}>
            {averageSentiment.toFixed(3)}
          </span>
        </div>
        <div className="flex justify-between text-sm mt-1">
          <span className="text-gray-500">Range:</span>
          <span className="font-medium text-gray-900">
            {sentimentData.min_sentiment.toFixed(2)} to {sentimentData.max_sentiment.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
}