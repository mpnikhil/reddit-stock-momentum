import React from 'react';
import { TimeRange } from '../types';

interface TimeRangeSelectorProps {
  value: TimeRange;
  onChange: (range: TimeRange) => void;
  className?: string;
}

const timeRanges: { value: TimeRange; label: string; days: number }[] = [
  { value: '1d', label: '1 Day', days: 1 },
  { value: '3d', label: '3 Days', days: 3 },
  { value: '7d', label: '7 Days', days: 7 },
  { value: '30d', label: '30 Days', days: 30 },
];

export default function TimeRangeSelector({ value, onChange, className = '' }: TimeRangeSelectorProps) {
  return (
    <div className={`flex space-x-1 bg-gray-100 rounded-lg p-1 ${className}`}>
      {timeRanges.map((range) => (
        <button
          key={range.value}
          onClick={() => onChange(range.value)}
          className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
            value === range.value
              ? 'bg-white text-primary-700 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          {range.label}
        </button>
      ))}
    </div>
  );
}

export function timeRangeToDays(range: TimeRange): number {
  const rangeMap = { '1d': 1, '3d': 3, '7d': 7, '30d': 30 };
  return rangeMap[range];
}