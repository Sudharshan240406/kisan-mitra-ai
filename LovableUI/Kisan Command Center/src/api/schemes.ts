import { mockRequest } from "./client";

export type Scheme = {
  id: string;
  name: string;
  ministry: string;
  benefit: string;
  deadline: string;
  eligibility: string[];
  documents: string[];
  status: "Open" | "Closing soon" | "Closed";
  enrolled: number;
};

export type SchemeEligibility = { id: string; name: string; eligible: boolean; reason: string };
export type SchemeApplication = { id: string; farmer: string; scheme: string; stage: string; updatedAt: string };

export const schemesApi = {
  list: () => mockRequest("/schemes", (): Scheme[] => []),
  eligibility: (_farmerId: string) =>
    mockRequest(`/schemes/eligibility/${_farmerId}`, (): SchemeEligibility[] => []),
  applications: () =>
    mockRequest("/schemes/applications", (): SchemeApplication[] => []),
};
