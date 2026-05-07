import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for fetching API data with loading/error/empty states
 * Supports AbortController for cancelling in-flight requests on rapid filter changes.
 */
export function useApiData(fetchFn, deps = [], options = {}) {
  const { immediate = true, initialData = null } = options;
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);
  const mountedRef = useRef(true);
  const abortControllerRef = useRef(null);
  const requestIdRef = useRef(0);

  const fetch = useCallback(async (...args) => {
    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new AbortController for this request
    const controller = new AbortController();
    abortControllerRef.current = controller;
    const currentRequestId = ++requestIdRef.current;

    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn(...args);
      // Only update state if this is still the latest request and component is mounted
      if (mountedRef.current && currentRequestId === requestIdRef.current) {
        setData(result);
        setLoading(false);
      }
      return result;
    } catch (e) {
      // Ignore aborted requests
      if (e?.name === 'AbortError' || e?.code === 'ERR_CANCELED') {
        return null;
      }
      if (mountedRef.current && currentRequestId === requestIdRef.current) {
        setError(e.message || 'An error occurred');
        setLoading(false);
      }
      return null;
    }
  }, [fetchFn]);

  const retry = useCallback(() => {
    fetch();
  }, [fetch]);

  useEffect(() => {
    mountedRef.current = true;
    if (immediate) {
      fetch();
    }
    return () => {
      mountedRef.current = false;
      // Abort any in-flight request on unmount or dep change
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error, retry, refetch: fetch, setData };
}
