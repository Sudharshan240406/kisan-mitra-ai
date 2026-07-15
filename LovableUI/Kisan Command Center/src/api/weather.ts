import { mockRequest } from "./client";

export type WeatherSummary = {
  location: string;
  updatedAt: string;
  tempC: number | null;
  feelsLike: number | null;
  humidity: number | null;
  windKmh: number | null;
  pressureHpa: number | null;
  uvIndex: number | null;
  dewPointC: number | null;
  rainMm24h: number | null;
  cloudCover: number | null;
} | null;

export type ForecastDay = { day: string; date: string; tempMax: number; tempMin: number; rainProb: number; windKmh: number; humidity: number; note: string };
export type WeatherAlert = { id: string; region: string; type: string; severity: "info" | "watch" | "warning" | "severe"; validFor: string; issuedAt: string };

export const weatherApi = {
  currentSummary: (_location = "") =>
    mockRequest(`/weather/summary`, (): WeatherSummary => null),
  forecast7: () => mockRequest("/weather/forecast", (): ForecastDay[] => []),
  alerts: () => mockRequest("/weather/alerts", (): WeatherAlert[] => []),
};
