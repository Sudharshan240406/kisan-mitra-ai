import { mockRequest } from "./client";

export type Farmer = {
  id: string;
  name: string;
  phone: string;
  village: string;
  district: string;
  state: string;
  language: "Hindi" | "Marathi" | "Telugu" | "Tamil" | "Punjabi" | "Kannada" | "Bengali";
  crop: string;
  crops: string[];
  landHa: number;
  soil: "Alluvial" | "Black" | "Red" | "Laterite" | "Sandy";
  irrigation: "Drip" | "Sprinkler" | "Canal" | "Rainfed" | "Borewell";
  status: "Active" | "Onboarding" | "Dormant";
  enrolledOn: string;
  lastContactedOn: string;
  aadhaarMasked: string;
  kccLimit: number;
  schemes: string[];
};

export type FarmerFilters = { q?: string; state?: string; status?: Farmer["status"] };

export type FarmerTimelineEntry = { at: string; kind: string; text: string };

export const farmersApi = {
  list: (_filters: FarmerFilters = {}) =>
    mockRequest("/farmers", (): Farmer[] => []),
  get: (_id: string) =>
    mockRequest(`/farmers/${_id}`, (): Farmer | null => null),
  timeline: (_id: string) =>
    mockRequest(`/farmers/${_id}/timeline`, (): FarmerTimelineEntry[] => []),
  states: () =>
    mockRequest("/farmers/facets/states", (): string[] => []),
};
