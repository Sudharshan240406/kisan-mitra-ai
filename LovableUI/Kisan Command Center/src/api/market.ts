import { mockRequest } from "./client";

export type MandiPrice = {
  commodity: string;
  mandi: string;
  state: string;
  priceQuintal: number;
  change24h: number;
  forecast7d: number;
  demand: "Low" | "Steady" | "High" | "Surging";
};

export type PriceHistoryPoint = { day: number; price: number };

export const marketApi = {
  prices: () => mockRequest("/market/prices", (): MandiPrice[] => []),
  gainers: () => mockRequest("/market/gainers", (): MandiPrice[] => []),
  losers: () => mockRequest("/market/losers", (): MandiPrice[] => []),
  history: (commodity: string) =>
    mockRequest(`/market/history/${commodity}`, (): PriceHistoryPoint[] => []),
};
