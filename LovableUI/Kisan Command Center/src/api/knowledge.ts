import { mockRequest } from "./client";

export type KnowledgeCard = {
  id: string;
  title: string;
  category: "Advisory" | "Circular" | "Best practice" | "Research";
  crop?: string;
  updatedAt: string;
  source: string;
  excerpt: string;
};

export const knowledgeApi = {
  list: (_q?: string, _category?: KnowledgeCard["category"]) =>
    mockRequest("/knowledge", (): KnowledgeCard[] => []),
};
