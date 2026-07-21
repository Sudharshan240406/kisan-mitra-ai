"use client";

import React, { useState } from "react";
import { useDashboard } from "@/components/DashboardContext";
import { Cpu, Wifi, WifiOff, Bell, User, AlertTriangle, ShieldCheck, ChevronDown, Check, Phone } from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";

import { getApiBase, getWsBase } from "@/lib/utils";

const API_BASE = getApiBase();
const WS_BASE = getWsBase();

interface TopNavigationProps {
  onOpenDemo?: () => void;
}

export default function TopNavigation({ onOpenDemo }: TopNavigationProps = {}) {

  const {
    sessionId,
    alerts,
    aiSummary,
    metrics,
    featureFlags
  } = useDashboard();

  // Get active live connection state from useWebSocket inside components or use context
  // Wait, let's use the live WebSocket details. Since page.tsx or MissionControl has useWebSocket,
  // we can use a separate hook instantiation or get it from context. Let's subscribe to WS in context or use a local ws hook.
  // Actually, we can use useWebSocket inside the DashboardProvider, or we can instantiate it here to show live connection!
  // To keep it simple, DashboardProvider or hook can manage it. Let's look up connection status from useWebSocket.
  // Let's connect using the hook here.
  const { isConnected, clientCount } = useWebSocket({
    url: `${WS_BASE}/ws/live`,
  });

  const [showAlerts, setShowAlerts] = useState(false);
  const [showProfile, setShowProfile] = useState(false);

  const budgetUsedPercent = aiSummary?.budget_utilization_percent ?? 0;
  const accumulatedCost = aiSummary?.accumulated_cost_usd ?? 0;
  const currentModel = featureFlags.modelName || "gemini-1.5-pro";

  return (
    <header className="border-b border-slate-900/60 bg-slate-950/45 backdrop-blur-md sticky top-0 z-50 px-6 py-3 flex items-center justify-between transition-all select-none">
      {/* Brand Logo */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/10 transition-all duration-300 hover:rotate-6">
          <Cpu className="w-4.5 h-4.5 text-slate-950 animate-pulse" />
        </div>
        <div>
          <h1 className="text-sm font-black tracking-widest bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 via-teal-300 to-sky-200">
            KISAN MITRA AI
          </h1>
          <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Enterprise Multi-Agent Platform</p>
        </div>
      </div>

      {/* Center Section: Connection & Gemini Status Gauges */}
      <div className="hidden md:flex items-center gap-6">
        {/* WebSocket Status */}
        <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full border text-[10px] font-bold uppercase tracking-wider transition-all ${
          isConnected
            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/25"
            : "bg-red-500/10 text-red-400 border-red-500/20"
        }`}>
          {isConnected ? <Wifi className="w-3.5 h-3.5 animate-pulse" /> : <WifiOff className="w-3.5 h-3.5" />}
          {isConnected ? `Connected (${clientCount})` : "Offline"}
        </div>

        {/* Gemini Engine Status */}
        <div className="flex items-center gap-3 bg-slate-900/40 px-3.5 py-1.5 rounded-xl border border-slate-800/60 text-[10px] text-slate-400">
          <span className="font-semibold text-slate-500">Model:</span>
          <span className="font-mono text-emerald-400 font-bold uppercase">{currentModel}</span>
          <div className="h-3 w-px bg-slate-800" />
          <span className="font-semibold text-slate-500">Budget:</span>
          <span className="font-mono text-slate-200 font-bold">${accumulatedCost.toFixed(3)}</span>
          <div className="w-12 bg-slate-950 h-1.5 rounded-full overflow-hidden">
            <div 
              className="bg-emerald-500 h-full rounded-full transition-all duration-500" 
              style={{ width: `${Math.min(budgetUsedPercent, 100)}%` }}
            />
          </div>
          <span className="font-bold text-[9px] text-slate-500">{budgetUsedPercent}%</span>
        </div>
      </div>

      {/* Right Controls: Phone Demo, Notifications & Profile */}
      <div className="flex items-center gap-3">
        {/* Launch Phone Demo Button */}
        {onOpenDemo && (
          <button
            onClick={onOpenDemo}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white text-xs font-bold shadow-lg shadow-emerald-950/50 border border-emerald-300/30 transition duration-200 cursor-pointer animate-pulse"
          >
            <Phone className="w-3.5 h-3.5" />
            <span>✦ Launch Phone Demo</span>
          </button>
        )}

        {/* Alerts Dropdown */}

        <div className="relative">
          <button 
            onClick={() => {
              setShowAlerts(!showAlerts);
              setShowProfile(false);
            }}
            className="p-2 bg-slate-900/60 hover:bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800/80 rounded-xl transition duration-200 relative cursor-pointer"
          >
            <Bell className="w-4 h-4" />
            {alerts.length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-amber-500 text-[9px] font-black text-slate-950 rounded-full flex items-center justify-center animate-bounce">
                {alerts.length}
              </span>
            )}
          </button>

          {showAlerts && (
            <div className="absolute right-0 mt-2 w-64 bg-slate-950/95 border border-slate-850 rounded-2xl shadow-xl backdrop-blur-md p-3 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
              <div className="flex items-center justify-between border-b border-slate-900 pb-2 mb-2">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Alerts Stream</span>
                <span className="text-[9px] text-slate-600">Trace Logs</span>
              </div>
              <div className="flex flex-col gap-2 max-h-48 overflow-y-auto mc-scrollbar">
                {alerts.length === 0 ? (
                  <span className="text-[10px] text-slate-600 italic block py-2 text-center">No alerts logged.</span>
                ) : (
                  alerts.slice(0, 10).map((alert, i) => (
                    <div key={i} className="text-[10px] leading-relaxed border-l border-slate-800 pl-2 py-0.5">
                      <span className={`font-bold uppercase text-[9px] ${
                        alert.type === "error" ? "text-red-400" : alert.type === "warn" ? "text-amber-400" : "text-sky-400"
                      }`}>{alert.type}:</span>
                      <p className="text-slate-300 mt-0.5">{alert.msg}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Profile Dropdown */}
        <div className="relative">
          <button 
            onClick={() => {
              setShowProfile(!showProfile);
              setShowAlerts(false);
            }}
            className="flex items-center gap-1.5 p-1.5 pr-2.5 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/80 rounded-xl transition duration-200 cursor-pointer"
          >
            <div className="w-6.5 h-6.5 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-[11px] border border-emerald-500/10">
              A
            </div>
            <span className="text-[10px] font-bold text-slate-300 hidden sm:block">Admin</span>
            <ChevronDown className="w-3 h-3 text-slate-500" />
          </button>

          {showProfile && (
            <div className="absolute right-0 mt-2 w-48 bg-slate-950/95 border border-slate-850 rounded-2xl shadow-xl backdrop-blur-md p-2 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
              <div className="p-2 border-b border-slate-900">
                <p className="text-xs font-bold text-slate-200">Kisan Mitra Admin</p>
                <p className="text-[9px] text-slate-500 mt-0.5">administrator@kisanmitra.org</p>
              </div>
              <div className="flex flex-col gap-0.5 mt-1">
                <button className="w-full text-left px-2 py-1.5 text-[10px] text-slate-300 hover:bg-slate-900 rounded-lg transition">
                  Platform Diagnostics
                </button>
                <button className="w-full text-left px-2 py-1.5 text-[10px] text-slate-300 hover:bg-slate-900 rounded-lg transition">
                  Account Credentials
                </button>
                <div className="h-px bg-slate-900 my-1" />
                <div className="px-2 py-1.5 text-[9px] text-slate-600 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Role: System Architect
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
