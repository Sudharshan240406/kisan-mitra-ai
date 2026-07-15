import { mockRequest } from "./client";

export type Alert = {
  id: string;
  severity: "info" | "warning" | "critical";
  category: "weather" | "market" | "pest" | "system" | "scheme";
  title: string;
  description: string;
  region?: string;
  createdAt: string;
  acknowledged: boolean;
};

export const alertsApi = {
  list: () => mockRequest("/alerts", (): Alert[] => []),
  acknowledge: (id: string) =>
    mockRequest(`/alerts/${id}/ack`, () => ({ id, acknowledged: true })),
};
