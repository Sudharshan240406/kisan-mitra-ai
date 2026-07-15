import { mockRequest } from "./client";

export type FarmerGrowthPoint = { month: string; farmers: number; aiCalls: number };
export type DistrictRow = { district: string; state: string; farmers: number; adoption: number; avgYieldChange: number };
export type SchemeUtil = { scheme: string; pct: number };

export const analyticsApi = {
  farmerGrowth: () => mockRequest("/analytics/farmer-growth", (): FarmerGrowthPoint[] => []),
  districts: () => mockRequest("/analytics/districts", (): DistrictRow[] => []),
  schemeUtilization: () => mockRequest("/analytics/schemes", (): SchemeUtil[] => []),
};
