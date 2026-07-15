import { mockRequest } from "./client";

export type Provider = {
  id: string;
  name: string;
  region: string;
  status: "healthy" | "degraded" | "down";
  latencyMs: number;
  requests24h: number;
  errorRate: number;
  cost24hUsd: number;
};

export type Model = {
  id: string;
  name: string;
  provider: string;
  kind: "LLM" | "Vision" | "Speech" | "Embeddings" | "Forecast";
  tokensInK: number;
  tokensOutK: number;
  costUsd: number;
  p95LatencyMs: number;
  confidence: number;
  fallback?: string;
  status: "healthy" | "degraded" | "down";
};

export type RoutingDecision = { at: string; from: string; to: string; reason: string; count: number };

export const aiApi = {
  providers: () => mockRequest("/ai/providers", (): Provider[] => []),
  models: () => mockRequest("/ai/models", (): Model[] => []),
  routingDecisions: () => mockRequest("/ai/routing", (): RoutingDecision[] => []),
};
