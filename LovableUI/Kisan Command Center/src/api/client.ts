// Centralized API client. The mock/demo layer has been fully removed —
// `mockRequest` is retained only as a compatibility shim so existing API
// modules keep the same call shape, but its producers now yield empty
// datasets (arrays of length 0, or null). Replace with `apiRequest` once
// the FastAPI backend is live.

export type ApiError = { status: number; message: string; code?: string };

export type ApiResponse<T> = {
  data: T;
  meta?: { page?: number; total?: number; latencyMs?: number };
};

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

/**
 * Deprecated: no simulated latency, no randomness, no fabricated data.
 * Producers passed in MUST return empty datasets — this file will disappear
 * entirely once every module switches to `apiRequest`.
 */
export async function mockRequest<T>(
  _path: string,
  producer: () => T | Promise<T>,
): Promise<ApiResponse<T>> {
  const data = await producer();
  return { data, meta: { latencyMs: 0 } };
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<ApiResponse<T>> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
  });
  if (!res.ok) throw { status: res.status, message: res.statusText } as ApiError;
  return (await res.json()) as ApiResponse<T>;
}
