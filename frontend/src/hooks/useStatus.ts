/**
 * useStatus Hook - Handles system status checks
 */

import { useState, useEffect, useCallback } from 'react';
import { getStatus } from '@/lib/api';
import type { StatusData } from '@/types/api';

export function useStatus() {
  const [status, setStatus] = useState<StatusData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getStatus();

      if (response.success && response.data) {
        setStatus(response.data);
      } else {
        setError(response.error || 'Failed to fetch status');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch status';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return {
    status,
    isLoading,
    error,
    refresh: fetchStatus,
  };
}
