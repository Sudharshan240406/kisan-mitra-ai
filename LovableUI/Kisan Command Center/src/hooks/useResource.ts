import { useCallback, useEffect, useRef, useState } from "react";
import type { ApiError, ApiResponse } from "@/api/client";

export type ResourceState<T> = {
  data: T | null;
  error: ApiError | null;
  loading: boolean;      // first load, no data yet
  refreshing: boolean;   // background refetch, data already present
  isEmpty: boolean;
  isOffline: boolean;
  latencyMs?: number;
  refetch: () => void;
};

// Universal fetch-state hook. Every page uses this so loading / error /
// empty / refreshing behaviour is identical across the platform.
export function useResource<T>(
  fetcher: () => Promise<ApiResponse<T>>,
  deps: unknown[] = [],
): ResourceState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [latencyMs, setLatencyMs] = useState<number | undefined>();
  const [online, setOnline] = useState(true);
  const mounted = useRef(true);

  const load = useCallback(async () => {
    const hasData = data !== null;
    hasData ? setRefreshing(true) : setLoading(true);
    setError(null);
    try {
      const res = await fetcher();
      if (!mounted.current) return;
      setData(res.data);
      setLatencyMs(res.meta?.latencyMs);
    } catch (e) {
      if (!mounted.current) return;
      setError(e as ApiError);
    } finally {
      if (mounted.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    mounted.current = true;
    load();
    return () => { mounted.current = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    setOnline(navigator.onLine);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => { window.removeEventListener("online", on); window.removeEventListener("offline", off); };
  }, []);

  const isEmpty = !loading && !error && (
    data === null || (Array.isArray(data) && data.length === 0)
  );

  return { data, error, loading, refreshing, isEmpty, isOffline: !online, latencyMs, refetch: load };
}
