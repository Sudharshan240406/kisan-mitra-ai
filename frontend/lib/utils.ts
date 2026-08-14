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
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1" || /^(10|172\.(1[6-9]|2[0-9]|3[01])|192\.168)\./.test(host) || host.endsWith(".local")) {
      return `http://${host}:8000`;
    }
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
