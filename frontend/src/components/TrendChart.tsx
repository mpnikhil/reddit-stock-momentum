import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { TrendDataPoint } from '../types';
import { format } from 'date-fns';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface TrendChartProps {
  data: TrendDataPoint[];
  title: string;
  type: 'mentions' | 'sentiment' | 'momentum';
  className?: string;
}

export default function TrendChart({ data, title, type, className = '' }: TrendChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className={`card ${className}`}>
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <div className="flex items-center justify-center h-64 text-gray-500">
          No data available
        </div>
      </div>
    );
  }

  const labels = data.map(point => 
    format(new Date(point.date), 'MMM dd')
  );

  const getDatasetConfig = () => {
    switch (type) {
      case 'mentions':
        return {
          label: 'Mentions',
          data: data.map(point => point.mention_count),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
        };
      case 'sentiment':
        return {
          label: 'Sentiment',
          data: data.map(point => point.avg_sentiment),
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          tension: 0.4,
        };
      case 'momentum':
        return {
          label: 'Momentum Score',
          data: data.map(point => point.momentum_score),
          borderColor: 'rgb(249, 115, 22)',
          backgroundColor: 'rgba(249, 115, 22, 0.1)',
          tension: 0.4,
        };
      default:
        return {
          label: 'Value',
          data: [],
          borderColor: 'rgb(107, 114, 128)',
          backgroundColor: 'rgba(107, 114, 128, 0.1)',
        };
    }
  };

  const chartData = {
    labels,
    datasets: [getDatasetConfig()],
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        callbacks: {
          title: (context) => {
            const dataPoint = data[context[0].dataIndex];
            return format(new Date(dataPoint.date), 'MMM dd, yyyy');
          },
          afterLabel: (context) => {
            const dataPoint = data[context.dataIndex];
            const extras = [];
            
            if (type === 'mentions') {
              extras.push(`Posts: ${dataPoint.unique_posts}`);
              extras.push(`Sentiment: ${dataPoint.avg_sentiment.toFixed(2)}`);
            } else if (type === 'sentiment') {
              extras.push(`Mentions: ${dataPoint.mention_count}`);
              extras.push(`Momentum: ${dataPoint.momentum_score.toFixed(1)}%`);
            } else if (type === 'momentum') {
              extras.push(`Mentions: ${dataPoint.mention_count}`);
              extras.push(`Volume Spike: ${dataPoint.volume_spike.toFixed(1)}%`);
            }
            
            return extras;
          },
        },
      },
    },
    scales: {
      x: {
        display: true,
        grid: {
          display: false,
        },
      },
      y: {
        display: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
        beginAtZero: type === 'mentions',
        ticks: {
          callback: function(value) {
            if (type === 'sentiment') {
              return typeof value === 'number' ? value.toFixed(2) : value;
            }
            if (type === 'momentum') {
              return typeof value === 'number' ? `${value.toFixed(0)}%` : value;
            }
            return value;
          },
        },
      },
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false,
    },
  };

  return (
    <div className={`card ${className}`}>
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <div className="h-64">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}