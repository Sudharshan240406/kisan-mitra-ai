import { mockRequest } from "./client";

export type Conversation = {
  id: string;
  farmer: string;
  channel: "IVR" | "WhatsApp" | "SMS" | "App";
  language: string;
  durationSec: number;
  sentiment: "positive" | "neutral" | "negative";
  confidence: number;
  intent: string;
  summary: string;
  evidence: string[];
  startedAt: string;
};

export const conversationsApi = {
  list: () => mockRequest("/conversations", (): Conversation[] => []),
  get: (_id: string) => mockRequest(`/conversations/${_id}`, (): Conversation | null => null),
};
