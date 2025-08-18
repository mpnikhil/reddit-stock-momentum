import { useState, useEffect, useCallback } from 'react';
import { ApiResponse } from '../types';

export function useApi<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = []
): ApiResponse<T> & { refetch: () => void } {
  const [data, setData] = useState<T | undefined>(undefined);
  const [error, setError] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(undefined);
      const result = await apiCall();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setData(undefined);
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    error,
    loading,
    refetch: fetchData,
  };
}

export function usePolling<T>(
  apiCall: () => Promise<T>,
  interval: number = 30000, // 30 seconds default
  dependencies: any[] = []
): ApiResponse<T> & { refetch: () => void } {
  const apiResponse = useApi(apiCall, dependencies);

  useEffect(() => {
    if (!apiResponse.loading && !apiResponse.error) {
      const intervalId = setInterval(() => {
        apiResponse.refetch();
      }, interval);

      return () => clearInterval(intervalId);
    }
  }, [apiResponse.loading, apiResponse.error, apiResponse.refetch, interval]);

  return apiResponse;
}