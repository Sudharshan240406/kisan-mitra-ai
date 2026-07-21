import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const RENDER_BACKEND_URL = "https://kisan-mitra-ai-jxp4.onrender.com";

export function getApiBase(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "");
  }
  if (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
    return RENDER_BACKEND_URL;
  }
  return "http://localhost:8000";
}

export function getWsBase(): string {
  const apiBase = getApiBase();
  if (apiBase.startsWith("https://")) {
    return apiBase.replace(/^https:\/\//, "wss://");
  }
  return apiBase.replace(/^http:\/\//, "ws://");
}
