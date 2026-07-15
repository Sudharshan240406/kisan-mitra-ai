import { mockRequest } from "./client";

export type ServiceHealth = { name: string; status: "healthy" | "degraded" | "down"; uptime: string; p95: number };

export type TelemetryMetrics = {
  cpuPct: number | null;
  memPct: number | null;
  requestsPerMin: number | null;
  errorsPerMin: number | null;
  p95LatencyMs: number | null;
};

export type TelemetryHistoryPoint = { t: number; req: number; err: number };

export const telemetryApi = {
  metrics: () =>
    mockRequest("/telemetry/metrics", (): TelemetryMetrics => ({
      cpuPct: null,
      memPct: null,
      requestsPerMin: null,
      errorsPerMin: null,
      p95LatencyMs: null,
    })),
  services: () => mockRequest("/telemetry/services", (): ServiceHealth[] => []),
  history: () => mockRequest("/telemetry/history", (): TelemetryHistoryPoint[] => []),
};
