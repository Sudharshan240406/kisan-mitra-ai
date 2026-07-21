"use client";

import React, { useState, useEffect, lazy, Suspense } from "react";
import dynamic from "next/dynamic";
import { DashboardProvider, useDashboard } from "@/components/DashboardContext";
import TopNavigation from "@/components/TopNavigation";
import LeftSidebar from "@/components/LeftSidebar";
import RightThinkingPanel from "@/components/RightThinkingPanel";
import { Hero } from "@/components/kisan/Hero";
import { KpiCard } from "@/components/kisan/KpiCard";
import { AgentGrid } from "@/components/kisan/AgentGrid";
import { IndiaMap } from "@/components/kisan/IndiaMap";
import { WeatherPanel, MarketPanel, SchemesPanel, CommsPanel, AlertsPanel } from "@/components/kisan/Panels";
import { BackgroundFX } from "@/components/kisan/BackgroundFX";
import WelfareSchemes from "@/components/WelfareSchemes";
import AIExplainability from "@/components/AIExplainability";
import AnalyticsCenter from "@/components/AnalyticsCenter";
import PresentationDemo from "@/components/PresentationDemo";
import { DemoModeModal } from "@/components/demo/DemoModeModal";
import { Users, MessageCircle, Landmark, Sparkles, Bot, MapPin } from "lucide-react";


const MissionControl = dynamic(() => import("@/components/MissionControl"), { ssr: false });
import {
  MessageSquare,
  CloudSun,
  TrendingUp,
  BookOpen,
  Award,
  Database,
  ShieldCheck,
  Search,
  Activity,
  Cpu,
  RefreshCw,
  AlertTriangle,
  ChevronRight,
  Play,
  Settings,
  Server,
  Terminal,
  Radio,
  List,
  Bell,
  Clock,
  Phone,
  Mail,
  HardDrive
} from "lucide-react";

// Types corresponding to Backend Abstractions
interface EvidenceItem {
  id: string;
  source: string;
  agent: string;
  confidence: number;
  weight: number;
  reasoning: string;
  citation?: string;
}

interface AdvisoryResponse {
  summary: string;
  recommendation: string;
  evidence: EvidenceItem[];
  confidence: number;
  risk: number;
  reasoning: string[];
  sources: string[];
  warnings: string[];
  missing_information: string[];
  follow_up_required: string[];
  safety_assessment: {
    is_safe: boolean;
    risk_score: number;
    flagged_reasons: string[];
    warnings: string[];
    safety_metrics: {
      total_checks_run: number;
      evidence_count_assessed: number;
      low_confidence_sources_count: number;
      invalid_sources_count: number;
    };
    planning?: {
      workflow_id: string;
      complexity: string;
      confidence: number;
      missing_fields: string[];
    };
  };
  reasoning_graph_ref?: string;
}

interface AgentHealth {
  name: string;
  role: string;
  status: "idle" | "running" | "ready" | "offline";
  latency: string;
  icon: React.ReactNode;
}

interface TelemetryMetrics {
  planning_latency: { avg_ms: number; count: number };
  workflow_latency: { avg_ms: number; count: number };
  decision_latency: { avg_ms: number; count: number };
  agent_execution_times: Record<string, number>;
  evidence_count_total: number;
  max_reasoning_depth: number;
  max_graph_size: number;
  confidence_distribution: number[];
  safety_interventions_count: number;
  policy_violations_count: number;
  max_memory_usage_bytes: number;
  channel_metrics: {
    messages_processed: number;
    avg_routing_latency_ms: number;
    avg_response_time_ms: number;
    avg_session_duration_seconds: number;
    channel_utilization: Record<string, number>;
    error_rate: number;
    error_count: number;
  };
  media_metrics: {
    total_processed: number;
    avg_processing_latency_ms: number;
    validation_failures: number;
    policy_violations: number;
    media_utilization: Record<string, number>;
  };
  voice_metrics: {
    total_sessions: number;
    avg_processing_latency_ms: number;
    avg_confidence: number;
  };
  vision_metrics: {
    total_uploads: number;
    avg_processing_latency_ms: number;
    avg_confidence: number;
  };
  ocr_metrics: {
    total_requests: number;
    avg_processing_latency_ms: number;
    avg_confidence: number;
  };
  multimodal_metrics: {
    total_processed: number;
    avg_processing_latency_ms: number;
    avg_confidence: number;
    reasoning_integration_rate: number;
  };
  telephony_metrics: {
    total_calls: number;
    avg_call_duration_seconds: number;
    ivr_completion_rate: number;
    avg_routing_latency_ms: number;
    total_retries: number;
    error_rate: number;
    error_count: number;
  };
  sms_metrics: {
    received_count: number;
    sent_count: number;
    delivery_rate: number;
    retry_count: number;
    avg_processing_latency_ms: number;
    validation_failures: number;
    policy_violations: number;
    avg_continuity: number;
    language_distribution: Record<string, number>;
  };
  integration_metrics?: {
    total_calls: number;
    avg_latency_ms: number;
    failure_count: number;
    retry_count: number;
    adapters: Record<string, any>;
  };
}

interface CallSession {
  call_id: string;
  caller: string;
  callee: string;
  status: string;
  direction: string;
  current_ivr_state: string;
  language: string;
  dtmf_input_buffer: string;
  conversation_id: string;
  start_time: number;
  duration_seconds?: number;
}

interface SMSSession {
  sms_session_id: string;
  conversation_id: string;
  phone_number: string;
  language: string;
  delivery_status: string;
  retry_count: number;
  state: string;
  created_at: number;
  last_activity: number;
  thread_history: Array<{ direction: string; text: string; timestamp: number }>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  return (
    <DashboardProvider>
      <DashboardContent />
    </DashboardProvider>
  );
}

function DashboardContent() {
  const {
    activeTab, setActiveTab,
    query, setQuery,
    sessionId, setSessionId,
    isLoading, setIsLoading,
    response, setResponse,
    error, setError,
    latency, setLatency,
    metrics, calls, smsSessions, integrations, systemLogs, alerts, knowledgeStatus,
    aiProviders, aiSummary,
    diagPrompt, setDiagPrompt,
    diagTask, setDiagTask,
    diagPref, setDiagPref,
    diagResponse, setDiagResponse,
    diagLoading, setDiagLoading,
    newBudgetLimit, setNewBudgetLimit,
    featureFlags, setFeatureFlags,
    agents, setAgents,
    sampleQueries, systemComponents,
    fetchLiveState, logEvent, handleQuerySubmit, cleanExpiredSessions,
    handleToggleIntegration, handleActivateIntegration, handleTestIntegration,
    updateBudgetLimit, toggleModelAvailability, runRouterDiagnostic
  } = useDashboard();

  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);


  const fallbackMetrics: any = {
    planning_latency: { avg_ms: 18.4, count: 12 },
    workflow_latency: { avg_ms: 145.2, count: 12 },
    decision_latency: { avg_ms: 12.8, count: 12 },
    agent_execution_times: { "Weather": 15, "Market": 20, "Knowledge": 25, "Planner": 5, "Memory": 4 },
    evidence_count_total: 32,
    max_reasoning_depth: 4,
    max_graph_size: 7,
    confidence_distribution: [0.85, 0.9, 0.78],
    safety_interventions_count: 1,
    policy_violations_count: 0,
    max_memory_usage_bytes: 8192,
    channel_metrics: {
      messages_processed: 12,
      avg_routing_latency_ms: 8.5,
      avg_response_time_ms: 155.0,
      avg_session_duration_seconds: 320.0,
      channel_utilization: { "sms-01": 5, "ivr-001": 7 },
      error_rate: 0.0,
      error_count: 0
    },
    media_metrics: {
      total_processed: 3,
      avg_processing_latency_ms: 120.4,
      validation_failures: 0,
      policy_violations: 0,
      media_utilization: { "voice-mock": 3 }
    },
    voice_metrics: {
      total_sessions: 3,
      avg_processing_latency_ms: 110.0,
      avg_confidence: 0.91
    },
    vision_metrics: {
      total_uploads: 2,
      avg_processing_latency_ms: 135.0,
      avg_confidence: 0.89
    },
    ocr_metrics: {
      total_requests: 1,
      avg_processing_latency_ms: 95.0,
      avg_confidence: 0.95
    },
    multimodal_metrics: {
      total_processed: 3,
      avg_processing_latency_ms: 120.4,
      avg_confidence: 0.92,
      reasoning_integration_rate: 1.0
    },
    telephony_metrics: {
      total_calls: 7,
      avg_call_duration_seconds: 45.2,
      ivr_completion_rate: 1.0,
      avg_routing_latency_ms: 6.8,
      total_retries: 0,
      error_rate: 0.0,
      error_count: 0
    },
    sms_metrics: {
      received_count: 5,
      sent_count: 5,
      delivery_rate: 1.0,
      retry_count: 0,
      avg_processing_latency_ms: 9.4,
      validation_failures: 0,
      policy_violations: 0,
      avg_continuity: 2.5,
      language_distribution: { "hi": 4, "en": 1 }
    }
  };

  const activeMetrics = metrics || fallbackMetrics;
  const budgetUsedPercent = aiSummary?.budget_utilization_percent ?? 0;
  const accumulatedCost = aiSummary?.accumulated_cost_usd ?? 0.0;
  
  const kpis: any[] = [
    { 
      label: "Active Farmers", 
      value: calls.filter(c => c.status !== "completed").length + smsSessions.filter(s => s.state !== "closed").length, 
      delta: 12, 
      icon: Users,
      tone: "lime", 
      data: [3, 5, 8, 4, 9, 12, 14, 11, 13, 10, 12, calls.filter(c => c.status !== "completed").length + smsSessions.filter(s => s.state !== "closed").length] 
    },
    { 
      label: "AI Requests · 24h", 
      value: activeMetrics?.channel_metrics?.messages_processed ?? 12, 
      delta: 8, 
      icon: Bot, 
      tone: "sky", 
      data: [8, 12, 10, 15, 20, 18, 22, 25, 24, 28, 30, activeMetrics?.channel_metrics?.messages_processed ?? 12] 
    },
    { 
      label: "Voice Calls Today", 
      value: activeMetrics?.telephony_metrics?.total_calls ?? 7, 
      delta: 15, 
      icon: Phone, 
      tone: "wheat", 
      data: [2, 4, 3, 5, 8, 6, 7, 9, 10, 12, 11, activeMetrics?.telephony_metrics?.total_calls ?? 7] 
    },
    { 
      label: "SMS Dispatched", 
      value: activeMetrics?.sms_metrics?.sent_count ?? 5, 
      delta: 5, 
      icon: MessageCircle, 
      tone: "leaf", 
      data: [1, 2, 4, 3, 5, 6, 8, 7, 9, 11, 10, activeMetrics?.sms_metrics?.sent_count ?? 5] 
    },
    { 
      label: "Welfare Schemes", 
      value: activeMetrics?.sms_metrics?.received_count ?? 8, 
      delta: 24, 
      icon: Landmark, 
      tone: "wheat", 
      data: [10, 15, 12, 18, 22, 20, 24, 28, 30, 32, 35, activeMetrics?.sms_metrics?.received_count ?? 8] 
    },
    { 
      label: "Active Providers", 
      value: integrations.filter(i => i.status === "active").length, 
      delta: 0, 
      icon: MapPin, 
      tone: "leaf", 
      data: [6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, integrations.filter(i => i.status === "active").length] 
    },
    { 
      label: "Avg Latency", 
      value: activeMetrics?.workflow_latency?.avg_ms ?? 145.2, 
      suffix: " ms",
      delta: -4, 
      icon: CloudSun, 
      tone: "sky", 
      data: [180, 165, 175, 160, 155, 150, 148, 142, 145, 140, 138, activeMetrics?.workflow_latency?.avg_ms ?? 145.2] 
    },
    { 
      label: "AI Cost Today", 
      prefix: "$",
      value: accumulatedCost, 
      delta: 18, 
      icon: Sparkles, 
      tone: "lime", 
      data: [0.05, 0.08, 0.12, 0.18, 0.22, 0.28, 0.35, 0.42, 0.48, 0.52, 0.58, accumulatedCost] 
    },
  ];


  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans select-none selection:bg-emerald-500 selection:text-slate-950">
      <BackgroundFX />
      
      <TopNavigation onOpenDemo={() => setIsDemoModalOpen(true)} />

      <DemoModeModal isOpen={isDemoModalOpen} onClose={() => setIsDemoModalOpen(false)} />

      {/* Main Core Layout Grid */}

      <div className="flex-1 flex flex-col md:flex-row h-[calc(100vh-53px)] overflow-hidden">
        
        <LeftSidebar />

        {/* Dynamic Display Panel */}
        <main className="flex-1 bg-slate-900/10 p-6 overflow-y-auto mc-scrollbar">
          
          {/* TAB 0: MISSION CONTROL */}
          {activeTab === "mission-control" && (
            <Suspense fallback={<div className="text-slate-500 text-sm p-8">Loading Mission Control...</div>}>
              <MissionControl />
            </Suspense>
          )}

          {/* TAB 1.2: WELFARE SCHEMES */}
          {activeTab === "schemes" && (
            <Suspense fallback={<div className="text-slate-500 text-sm p-8">Loading Welfare Schemes Advisor...</div>}>
              <WelfareSchemes />
            </Suspense>
          )}

          {/* TAB 1.1: PRESENTATION DEMO CENTER */}
          {activeTab === "demo" && (
            <Suspense fallback={<div className="text-slate-500 text-sm p-8">Loading Presentation Deck...</div>}>
              <PresentationDemo onOpenDemo={() => setIsDemoModalOpen(true)} />
            </Suspense>
          )}


          {/* TAB 1: OVERVIEW */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              <Hero />

              <section aria-label="Key metrics" className="mt-6 z-10 relative">
                <div className="mb-3 flex items-end justify-between px-1">
                  <div>
                    <div className="text-[9px] font-black uppercase tracking-[0.18em] text-[var(--lime-glow)]">
                      Realtime metrics
                    </div>
                    <h2 className="mt-0.5 font-display text-base font-bold sm:text-lg">Operations pulse</h2>
                  </div>
                  <div className="hidden items-center gap-1.5 text-[9px] font-black uppercase tracking-wider text-white/50 sm:flex">
                    <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Live connected
                  </div>
                </div>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  {kpis.map((k, i) => <KpiCard key={k.label} kpi={k} index={i} />)}
                </div>
              </section>

              <section className="grid grid-cols-1 gap-6 xl:grid-cols-12 z-10 relative">
                <div className="xl:col-span-8 space-y-6">
                  <IndiaMap />
                  <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                    <WeatherPanel />
                    <MarketPanel />
                  </div>
                </div>
                <div className="xl:col-span-4 space-y-6">
                  <AgentGrid />
                  <AlertsPanel />
                </div>
              </section>

              <section className="grid grid-cols-1 gap-6 lg:grid-cols-3 z-10 relative">
                <div className="lg:col-span-2">
                  <CommsPanel />
                </div>
                <SchemesPanel />
              </section>
            </div>
          )}

          {/* TAB 2: AI EXPLAINABILITY & TRUST CENTER */}
          {activeTab === "platform" && (
            <Suspense fallback={<div className="text-slate-500 text-sm p-8">Loading Explainability Center...</div>}>
              <AIExplainability />
            </Suspense>
          )}
          
          {/* TAB 3: AI PLATFORM CONTROL CENTER */}
          {activeTab === "ai" && (
            <div className="flex flex-col gap-6">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <Cpu className="w-5 h-5 text-emerald-400" /> AI Model Platform & Specialist Hub
              </h2>
              <p className="text-xs text-slate-400">
                Configure cloud/local adapters, track token throughput, update daily budget cap levels, and run diagnostics.
              </p>

              {/* Cost & Budget Summary Widgets */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-xl flex flex-col justify-between">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Accumulated cost</span>
                  <span className="text-2xl font-black text-emerald-400 mt-1">
                    ${aiSummary?.accumulated_cost_usd?.toFixed(4) || "0.0000"}
                  </span>
                  <div className="w-full bg-slate-950 h-1.5 rounded-full mt-2 overflow-hidden">
                    <div 
                      className="bg-emerald-500 h-full rounded-full transition-all" 
                      style={{ width: `${Math.min(aiSummary?.budget_utilization_percent || 0, 100)}%` }}
                    />
                  </div>
                  <span className="text-[9px] text-slate-500 mt-1">
                    {aiSummary?.budget_utilization_percent || 0}% of daily limit
                  </span>
                </div>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-xl flex flex-col justify-between">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Total Requests</span>
                  <span className="text-2xl font-black text-sky-400 mt-1">
                    {aiSummary?.total_requests || 0}
                  </span>
                  <span className="text-[9px] text-slate-500 mt-1">
                    Errors tracked: {aiSummary?.total_errors || 0}
                  </span>
                </div>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-xl flex flex-col justify-between">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Tokens Transacted</span>
                  <span className="text-2xl font-black text-indigo-400 mt-1">
                    {(aiSummary?.accumulated_input_tokens || 0) + (aiSummary?.accumulated_output_tokens || 0)}
                  </span>
                  <span className="text-[9px] text-slate-500 mt-1">
                    In: {aiSummary?.accumulated_input_tokens || 0} | Out: {aiSummary?.accumulated_output_tokens || 0}
                  </span>
                </div>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-xl flex flex-col justify-between">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Daily threshold</span>
                  <div className="flex gap-2 items-center mt-1">
                    <input 
                      type="text" 
                      value={newBudgetLimit}
                      onChange={(e) => setNewBudgetLimit(e.target.value)}
                      className="w-16 bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 text-center"
                    />
                    <button 
                      onClick={async () => {
                        const lim = parseFloat(newBudgetLimit);
                        if (!isNaN(lim)) {
                          await fetch(`${API_BASE}/api/v1/ai/budget`, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ daily_budget_usd: lim })
                          });
                          logEvent(`Daily AI budget limit successfully updated to $${lim.toFixed(2)}`, "info");
                          fetchLiveState();
                        }
                      }}
                      className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-[9px] font-bold rounded cursor-pointer"
                    >
                      Update
                    </button>
                  </div>
                  <span className="text-[9px] text-slate-500 mt-2">Active budget cutoff guard</span>
                </div>
              </div>

              {/* Models Specs Grid */}
              <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Model Registry & Live Providers</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-900 text-slate-500 font-bold">
                        <th className="pb-2">Model ID</th>
                        <th className="pb-2">Provider</th>
                        <th className="pb-2">Input / Output Cost (1M)</th>
                        <th className="pb-2">Avg Latency</th>
                        <th className="pb-2">Availability</th>
                        <th className="pb-2 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {aiProviders.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="text-center py-4 text-slate-650">No models registered. Start backend server.</td>
                        </tr>
                      ) : (
                        aiProviders.map((p) => (
                          <tr key={p.model_id} className="border-b border-slate-950 hover:bg-slate-900/10">
                            <td className="py-2.5 font-bold text-slate-200">{p.model_id}</td>
                            <td className="py-2.5 uppercase font-mono text-[10px] text-sky-400">{p.provider_name}</td>
                            <td className="py-2.5 font-mono text-slate-300">
                              ${p.cost_per_million_input.toFixed(2)} / ${p.cost_per_million_output.toFixed(2)}
                            </td>
                            <td className="py-2.5 text-slate-400">{p.average_latency_ms} ms</td>
                            <td className="py-2.5">
                              <span className={`px-2 py-0.5 rounded text-[9px] font-mono border ${
                                p.availability === "healthy"
                                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/25"
                                  : "bg-red-500/10 text-red-400 border-red-500/25"
                              }`}>
                                {p.availability}
                              </span>
                            </td>
                            <td className="py-2.5 text-right flex gap-1 justify-end">
                              <button 
                                onClick={async () => {
                                  const nextState = p.availability === "healthy" ? "offline" : "healthy";
                                  await fetch(`${API_BASE}/api/v1/ai/toggle`, {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ model_id: p.model_id, availability: nextState })
                                  });
                                  logEvent(`Toggled model '${p.model_id}' availability state to '${nextState}'`, "info");
                                  fetchLiveState();
                                }}
                                className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-[9px] rounded font-bold cursor-pointer"
                              >
                                Toggle
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* AI Platform Diagnostics Routing Sandbox */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5 flex flex-col gap-4">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">AI Platform Router Sandbox</h3>
                  <div className="flex flex-col gap-3">
                    <div>
                      <span className="text-[10px] text-slate-500">Diagnostic Prompt</span>
                      <textarea
                        value={diagPrompt}
                        onChange={(e) => setDiagPrompt(e.target.value)}
                        rows={2}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 mt-1 resize-none"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <span className="text-[10px] text-slate-500">Task Type</span>
                        <select
                          value={diagTask}
                          onChange={(e) => setDiagTask(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 mt-1"
                        >
                          <option value="advisory">advisory (Cheaper, Cost-aware)</option>
                          <option value="reasoning">reasoning (Smarter, Deep MCDA)</option>
                          <option value="planning">planning (Smarter, Fallback priority)</option>
                          <option value="translation">translation (Cheaper, Low-latency)</option>
                        </select>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500">Forced Provider (Optional)</span>
                        <select
                          value={diagPref}
                          onChange={(e) => setDiagPref(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-300 mt-1"
                        >
                          <option value="">None (Automatic Route)</option>
                          <option value="gemini">Google Gemini</option>
                          <option value="openai">OpenAI / Groq</option>
                          <option value="claude">Anthropic Claude</option>
                          <option value="ollama">Local Ollama</option>
                        </select>
                      </div>
                    </div>
                    <button 
                      onClick={async () => {
                        setDiagLoading(true);
                        setDiagResponse(null);
                        try {
                          const res = await fetch(`${API_BASE}/api/v1/ai/test`, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                              prompt: diagPrompt,
                              task_type: diagTask,
                              preferred_provider: diagPref || null
                            })
                          });
                          const data = await res.json();
                          setDiagResponse(data);
                          if (data.status === "success") {
                            logEvent(`Diagnostics route resolved to model: ${data.routing.selected_model}`, "info");
                          } else {
                            logEvent(`Diagnostics route run failed: ${data.message}`, "error");
                          }
                        } catch (e) {
                          logEvent("Diagnostics network error", "error");
                        } finally {
                          setDiagLoading(false);
                          fetchLiveState();
                        }
                      }}
                      className="w-full py-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:shadow-lg hover:shadow-emerald-500/10 text-slate-950 text-xs font-bold rounded-xl cursor-pointer flex justify-center items-center gap-1.5 mt-2"
                    >
                      {diagLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : "Run Router Diagnostic"}
                    </button>
                  </div>
                </div>

                <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5 flex flex-col justify-between">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Diagnostics Output Trace</h3>
                  {diagResponse ? (
                    <div className="flex-1 flex flex-col gap-3 max-h-56 overflow-y-auto text-xs">
                      {diagResponse.status === "success" ? (
                        <>
                          <div className="p-2.5 bg-slate-950 border border-slate-900 rounded-lg">
                            <span className="text-[10px] text-slate-500 font-bold block uppercase">Routing Decision</span>
                            <p className="font-bold text-emerald-400 mt-0.5">{diagResponse.routing.selected_model}</p>
                            <p className="text-[10px] text-slate-400 mt-1">{diagResponse.routing.reason}</p>
                          </div>
                          <div className="p-2.5 bg-slate-950 border border-slate-900 rounded-lg flex-1">
                            <span className="text-[10px] text-slate-500 font-bold block uppercase">Output Payload Content</span>
                            <p className="text-slate-300 font-mono text-[10px] mt-1 whitespace-pre-wrap leading-relaxed">{diagResponse.response.content}</p>
                          </div>
                          <div className="grid grid-cols-3 gap-2 text-center text-[10px] text-slate-500 bg-slate-950/60 p-2 rounded-lg font-mono">
                            <div>
                              <span>Tokens in/out</span>
                              <p className="text-slate-300 font-bold mt-0.5">{diagResponse.response.prompt_tokens}/{diagResponse.response.completion_tokens}</p>
                            </div>
                            <div>
                              <span>Calculated cost</span>
                              <p className="text-emerald-400 font-bold mt-0.5">${diagResponse.response.cost.toFixed(5)}</p>
                            </div>
                            <div>
                              <span>Latency</span>
                              <p className="text-sky-400 font-bold mt-0.5">{diagResponse.response.latency_ms.toFixed(0)} ms</p>
                            </div>
                          </div>
                        </>
                      ) : (
                        <div className="p-3 bg-red-950/10 border border-red-900/20 text-red-400 rounded-lg">
                          Error: {diagResponse.message}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="flex-1 flex items-center justify-center text-slate-600 text-xs border border-dashed border-slate-900 rounded-xl p-4 min-h-44">
                      Submit a test prompt to inspect routing decisions.
                    </div>
                  )}
                </div>
              </div>

              {/* AI Specialist Hub Cards */}
              <div className="mt-2">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Specialist Workers Node Mappings</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {agents.map((agent) => (
                    <div key={agent.name} className="p-4 bg-slate-900/40 border border-slate-800 rounded-2xl flex items-start gap-4">
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-900">
                        {agent.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-slate-200">{agent.name}</h4>
                          <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            {agent.status}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-500 mt-1 leading-relaxed">{agent.role}</p>
                        <p className="text-[9px] font-mono text-slate-500 mt-1">Average response duration: {agent.latency}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: CONVERSATIONS */}
          {activeTab === "conversations" && (
            <div className="flex flex-col gap-6">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <List className="w-5 h-5 text-emerald-400" /> Conversations Monitor
              </h2>
              <p className="text-xs text-slate-400">
                Platform is monitoring active threads, language preferences, and average session times across SMS and IVR loops.
              </p>

              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-slate-400">Total sessions: {smsSessions.length + calls.length}</span>
                <button 
                  onClick={cleanExpiredSessions}
                  className="px-3 py-1.5 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl text-[10px] font-bold tracking-wider text-slate-300 cursor-pointer"
                >
                  Force Session Expiration Cleanups
                </button>
              </div>

              {smsSessions.length === 0 && calls.length === 0 ? (
                <div className="p-8 bg-slate-900/30 border border-slate-900 rounded-2xl text-center text-xs text-slate-500">
                  No active session threads logged. Run query in playground or simulate call webhook.
                </div>
              ) : (
                <div className="flex flex-col gap-4">
                  {smsSessions.map((s) => (
                    <div key={s.sms_session_id} className="p-4 bg-slate-900/40 border border-slate-800 rounded-2xl flex flex-col gap-2">
                      <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                        <span className="font-bold text-emerald-400">CHANNEL: SMS</span>
                        <span>Session ID: {s.sms_session_id.slice(0, 12)}...</span>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs mt-2 border-t border-b border-slate-900 py-3">
                        <div>
                          <span className="text-[10px] text-slate-500">Phone Number</span>
                          <p className="font-bold mt-1 text-slate-300">{s.phone_number}</p>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500">Language Preferred</span>
                          <p className="font-bold mt-1 text-indigo-400 uppercase">{s.language}</p>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500">Delivery Status</span>
                          <p className="font-bold mt-1 text-slate-300">{s.delivery_status}</p>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500">Retry State</span>
                          <p className="font-bold mt-1 text-slate-300">{s.retry_count}</p>
                        </div>
                      </div>
                    </div>
                  ))}

                  {calls.map((c) => (
                    <div key={c.call_id} className="p-4 bg-slate-900/40 border border-slate-800 rounded-2xl flex flex-col gap-2">
                      <div className="flex justify-between items-center text-[10px] font-mono text-slate-400">
                        <span className="font-bold text-sky-400">CHANNEL: IVR</span>
                        <span>Call ID: {c.call_id}</span>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs mt-2 border-t border-b border-slate-900 py-3">
                        <div>
                          <span className="text-[10px] text-slate-500">Caller URI</span>
                          <p className="font-bold mt-1 text-slate-300">{c.caller}</p>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500">IVR Node State</span>
                          <p className="font-bold mt-1 text-sky-400 uppercase">{c.current_ivr_state}</p>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500">Active DTMF Input</span>
                          <p className="font-bold mt-1 text-slate-300">"{c.dtmf_input_buffer || "None"}"</p>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500">Call Status</span>
                          <p className="font-bold mt-1 text-slate-300 uppercase">{c.status}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 5: MEDIA INGESTION */}
          {activeTab === "media" && (
            <div className="flex flex-col gap-6">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <HardDrive className="w-5 h-5 text-emerald-400" /> Media Ingestion Monitor
              </h2>
              <p className="text-xs text-slate-400">
                Audits multi-modal documents, speech voicemail uploads, and sensor anomaly inputs processed via the unified Media Pipeline.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-center">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Total Files Logged</span>
                  <p className="text-2xl font-black text-emerald-400 mt-2">{activeMetrics.media_metrics.total_processed}</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-center">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Validation Failures</span>
                  <p className="text-2xl font-black text-emerald-400 mt-2">{activeMetrics.media_metrics.validation_failures}</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-center">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Policy Blocks</span>
                  <p className="text-2xl font-black text-emerald-400 mt-2">{activeMetrics.media_metrics.policy_violations}</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-center">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Reasoning Integration</span>
                  <p className="text-2xl font-black text-emerald-400 mt-2">{(activeMetrics.multimodal_metrics.reasoning_integration_rate * 100).toFixed(0)}%</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-center">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Voice Sessions</span>
                  <p className="text-2xl font-black text-sky-400 mt-2">{activeMetrics.voice_metrics.total_sessions}</p>
                  <p className="text-[10px] text-slate-500 mt-1">{activeMetrics.voice_metrics.avg_processing_latency_ms.toFixed(0)}ms avg</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-center">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Vision Uploads</span>
                  <p className="text-2xl font-black text-amber-400 mt-2">{activeMetrics.vision_metrics.total_uploads}</p>
                  <p className="text-[10px] text-slate-500 mt-1">{(activeMetrics.vision_metrics.avg_confidence * 100).toFixed(0)}% avg confidence</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-center">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">OCR Requests</span>
                  <p className="text-2xl font-black text-indigo-400 mt-2">{activeMetrics.ocr_metrics.total_requests}</p>
                  <p className="text-[10px] text-slate-500 mt-1">{(activeMetrics.ocr_metrics.avg_confidence * 100).toFixed(0)}% avg confidence</p>
                </div>
              </div>

              {/* Media Util distribution */}
              <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5 mt-2">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 font-mono">Registered Media Providers</h3>
                <div className="flex flex-col gap-3">
                  {[
                    { id: "voice-mock", name: "Mock Voice Ingest STT", caps: "Speech-to-Text translation" },
                    { id: "image-mock", name: "Mock Image Ingest Ocr", caps: "Plant disease classification, OCR" },
                    { id: "doc-mock", name: "Mock Document Parser", caps: "Regulatory welfare matching parsing" },
                    { id: "sensor-mock", name: "Mock Sensor Ingestion", caps: "Soil moisture anomaly detection" }
                  ].map((p) => (
                    <div key={p.id} className="flex justify-between items-center p-3.5 bg-slate-950 border border-slate-900 rounded-xl">
                      <div>
                        <h4 className="text-xs font-bold text-slate-200">{p.name}</h4>
                        <p className="text-[9px] text-slate-500 mt-0.5">Capabilities: {p.caps}</p>
                      </div>
                      <span className="text-[9px] px-2 py-0.5 font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        active
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 6: TELEPHONY */}
          {activeTab === "telephony" && (
            <div className="flex flex-col gap-6">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <Phone className="w-5 h-5 text-emerald-400" /> Telephony & IVR Gateway
              </h2>
              <p className="text-xs text-slate-400">
                Platform is monitoring interactive telephony sessions. Outbound notifications can be triggered to basic offline dial-back queues.
              </p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">Total Calls</span>
                  <p className="text-2xl font-black text-emerald-400 mt-1">{activeMetrics.telephony_metrics.total_calls}</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">IVR Completion Rate</span>
                  <p className="text-2xl font-black text-sky-400 mt-1">{(activeMetrics.telephony_metrics.ivr_completion_rate * 100).toFixed(0)}%</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">Avg Call Duration</span>
                  <p className="text-2xl font-black text-indigo-400 mt-1">{(activeMetrics.telephony_metrics.avg_call_duration_seconds).toFixed(1)}s</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">SIP Retry Counts</span>
                  <p className="text-2xl font-black text-teal-400 mt-1">{activeMetrics.telephony_metrics.total_retries}</p>
                </div>
              </div>

              {/* Call sessions details */}
              <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Active Telephony Connections</h3>
                {calls.length === 0 ? (
                  <span className="text-xs text-slate-500">No active calls in progress.</span>
                ) : (
                  <div className="flex flex-col gap-3">
                    {calls.map((c) => (
                      <div key={c.call_id} className="flex justify-between items-center p-3 bg-slate-950 border border-slate-900 rounded-xl text-xs">
                        <div>
                          <strong className="text-slate-200">Caller: {c.caller}</strong>
                          <p className="text-[9px] text-slate-500 mt-0.5">Session: {c.conversation_id}</p>
                        </div>
                        <div className="text-right">
                          <span className="text-[9px] px-2 py-0.5 rounded font-mono bg-sky-500/10 text-sky-400 border border-sky-500/20 uppercase">
                            IVR State: {c.current_ivr_state}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 7: SMS GATEWAY */}
          {activeTab === "sms" && (
            <div className="flex flex-col gap-6">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <Mail className="w-5 h-5 text-emerald-400" /> SMS Intelligence Gateway
              </h2>
              <p className="text-xs text-slate-400">
                universal SMS alerts template registry and low-bandwidth threads monitor.
              </p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                  <span className="text-[10px] text-slate-500">SMS Received</span>
                  <p className="text-2xl font-black text-emerald-400 mt-1">{activeMetrics.sms_metrics.received_count}</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                  <span className="text-[10px] text-slate-500">SMS Outbound Sent</span>
                  <p className="text-2xl font-black text-sky-400 mt-1">{activeMetrics.sms_metrics.sent_count}</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                  <span className="text-[10px] text-slate-500">Validation Failures</span>
                  <p className="text-2xl font-black text-amber-500 mt-1">{activeMetrics.sms_metrics.validation_failures}</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                  <span className="text-[10px] text-slate-500">Language Preferred hi</span>
                  <p className="text-2xl font-black text-teal-400 mt-1">{activeMetrics.sms_metrics.language_distribution["hi"] || 0}</p>
                </div>
              </div>

              {/* Templates Engine */}
              <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Core Alert Templates Registry</h3>
                <div className="flex flex-col gap-3 font-serif">
                  {[
                    { key: "gov_scheme", hi: "किसान मित्र: नमस्ते {farmer_name}, नई सरकारी योजना '{scheme_name}' सक्रिय है। विवरण: {details}।" },
                    { key: "weather_alert", hi: "मौसम चेतावनी: {region} में मौसम {weather_condition} ({temp}C) रहेगा। कृपया सावधानी बरतें।" },
                    { key: "market_price", hi: "बाजार भाव: मंडी '{market}' में फसल {crop_name} का भाव रु {price}/क्विंटल है।" },
                    { key: "crop_advisory", hi: "फसल सलाह: {disease} के नियंत्रण हेतु सलाह: {recommendation}।" },
                    { key: "otp", hi: "आपका किसान मित्र ओटीपी कोड {otp_code} है। यह 10 मिनट के लिए मान्य है।" }
                  ].map((t) => (
                    <div key={t.key} className="p-3 bg-slate-950 border border-slate-900 rounded-xl text-xs leading-relaxed">
                      <strong className="text-indigo-400 font-mono text-[10px] uppercase tracking-wider block mb-1">Key: {t.key}</strong>
                      <span className="text-slate-300">"{t.hi}"</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 8: GOVERNANCE */}
          {activeTab === "governance" && (
            <div className="flex flex-col gap-6">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" /> Governance & Policy Engine
              </h2>
              <p className="text-xs text-slate-400">
                Audits policy violations, features toggles, and multi-agent credential registries.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-center">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Policy Evaluations run</span>
                  <p className="text-2xl font-black text-emerald-400 mt-2">
                    {activeMetrics.sms_metrics.received_count + activeMetrics.media_metrics.total_processed}
                  </p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-center">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Governance Interventions</span>
                  <p className="text-2xl font-black text-amber-500 mt-2">{activeMetrics.safety_interventions_count}</p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl text-center">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Policy Violations Blocked</span>
                  <p className="text-2xl font-black text-red-400 mt-2">{activeMetrics.policy_violations_count}</p>
                </div>
              </div>

              {/* Prompt catalogs */}
              <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Prompt Templates Registry Catalog</h3>
                <div className="flex flex-col gap-3 font-mono text-[10.5px]">
                  <div className="p-3 bg-slate-950 border border-slate-900 rounded-xl text-slate-300">
                    <span className="text-emerald-400 font-bold block mb-1">PLANNER_SYSTEM_PROMPT</span>
                    "You are the Lead Planning Agent. Formulate topological query schedules..."
                  </div>
                  <div className="p-3 bg-slate-950 border border-slate-900 rounded-xl text-slate-300">
                    <span className="text-emerald-400 font-bold block mb-1">VERIFIER_SAFETY_PROMPT</span>
                    "You are the Verifier Agent. Inspect agronomic advice outputs against safety guidelines..."
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 8.5: INTEGRATIONS PLATFORM */}
          {activeTab === "integrations" && (
            <div className="flex flex-col gap-6">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <RefreshCw className="w-5 h-5 text-emerald-400" /> External Integrations Platform
              </h2>
              <p className="text-xs text-slate-400">
                Manage registered adapters, hot-swap active providers, trigger diagnostics, and audit resilient metrics.
              </p>

              {/* Summary Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Total Calls</span>
                  <p className="text-2xl font-black text-emerald-400 mt-1">
                    {activeMetrics.integration_metrics?.total_calls ?? 0}
                  </p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Avg Latency</span>
                  <p className="text-2xl font-black text-sky-400 mt-1">
                    {(activeMetrics.integration_metrics?.avg_latency_ms ?? 0.0).toFixed(1)} ms
                  </p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Failure Count</span>
                  <p className="text-2xl font-black text-red-400 mt-1">
                    {activeMetrics.integration_metrics?.failure_count ?? 0}
                  </p>
                </div>
                <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Total Retries</span>
                  <p className="text-2xl font-black text-teal-400 mt-1">
                    {activeMetrics.integration_metrics?.retry_count ?? 0}
                  </p>
                </div>
              </div>

              {/* Integrations Table */}
              <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Registered Service Adapters</h3>
                
                {integrations.length === 0 ? (
                  <div className="p-8 text-center text-xs text-slate-500">
                    No integrations registered. Ensure backend server is running.
                  </div>
                ) : (
                  <div className="flex flex-col gap-4">
                    {integrations.map((i) => {
                      const adapterStats = activeMetrics.integration_metrics?.adapters?.[i.id] || {
                        avg_latency_ms: 0.0,
                        failures: 0,
                        retries: 0,
                        total_calls: 0
                      };

                      return (
                        <div key={i.id} className="p-4 bg-slate-950 border border-slate-900 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2.5">
                              <span className={`w-2 h-2 rounded-full ${
                                i.status === "active" ? "bg-emerald-500 animate-pulse" : i.status === "degraded" ? "bg-amber-500" : "bg-red-500"
                              }`} />
                              <h4 className="text-xs font-bold text-slate-200">{i.name}</h4>
                              <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 font-mono">v{i.version}</span>
                              <span className="text-[9px] px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 uppercase font-bold tracking-wider">{i.type}</span>
                              {i.is_active && (
                                <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 uppercase font-bold tracking-wider">Active Provider</span>
                              )}
                            </div>
                            <p className="text-[10px] text-slate-400 mt-1">{i.description}</p>
                            
                            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[9px] text-slate-500 font-mono">
                              <span>Capabilities: {i.capabilities.join(", ") || "None"}</span>
                              {i.configuration?.api_endpoint && (
                                <span>Endpoint: {i.configuration.api_endpoint}</span>
                              )}
                              {i.configuration?.portal_url && (
                                <span>Portal: {i.configuration.portal_url}</span>
                              )}
                            </div>
                          </div>

                          {/* Stats and Controls */}
                          <div className="flex items-center gap-4 flex-wrap md:flex-nowrap">
                            <div className="text-right text-[10px] font-mono text-slate-500 mr-2 border-r border-slate-900 pr-4 hidden sm:block">
                              <div>Calls: <span className="text-slate-300">{adapterStats.total_calls}</span></div>
                              <div>Lat: <span className="text-slate-300">{adapterStats.avg_latency_ms.toFixed(0)}ms</span></div>
                              <div>Retries/Fails: <span className="text-slate-300">{adapterStats.retries}/{adapterStats.failures}</span></div>
                            </div>

                            <div className="flex items-center gap-2">
                              {/* Status Toggle checkbox */}
                              <label className="flex items-center gap-1.5 cursor-pointer bg-slate-900/60 hover:bg-slate-900 px-2.5 py-1.5 rounded-lg border border-slate-800 transition duration-200 select-none">
                                <input
                                  type="checkbox"
                                  checked={i.status === "active"}
                                  onChange={() => handleToggleIntegration(i.id)}
                                  className="w-3.5 h-3.5 text-emerald-500 rounded border-slate-800 bg-slate-950 focus:ring-emerald-500"
                                />
                                <span className="text-[10px] text-slate-300 font-bold uppercase">Enabled</span>
                              </label>

                              {/* Activate button */}
                              {!i.is_active && i.status === "active" && (
                                <button
                                  onClick={() => handleActivateIntegration(i.id, i.type)}
                                  className="px-2.5 py-1.5 bg-slate-900 hover:bg-slate-850 text-[10px] text-slate-200 font-bold uppercase border border-slate-800 rounded-lg cursor-pointer transition duration-200"
                                >
                                  Activate
                                </button>
                              )}

                              {/* Test button */}
                              {i.status === "active" && (
                                <button
                                  onClick={() => handleTestIntegration(i.id)}
                                  className="px-2.5 py-1.5 bg-gradient-to-r from-emerald-500/25 to-teal-500/25 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold uppercase rounded-lg hover:from-emerald-500/35 hover:to-teal-500/35 cursor-pointer transition duration-200"
                                >
                                  Test
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 8B: KNOWLEDGE PLATFORM */}
          {activeTab === "knowledge" && (
            <div className="flex flex-col gap-6">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-emerald-400" /> Agricultural Knowledge Platform Control Center
              </h2>
              <p className="text-xs text-slate-400">
                Monitor registered knowledge base providers, index size metrics, cache hit parameters, and graph relationships.
              </p>

              {/* Status metrics grid */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-2xl flex flex-col justify-between">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Registered Databases</span>
                  <span className="text-3xl font-black text-emerald-400 mt-2">
                    {knowledgeStatus?.health?.registered_providers?.length || 10}
                  </span>
                  <span className="text-[9px] text-slate-500 mt-1">Active swappable providers</span>
                </div>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-2xl flex flex-col justify-between">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Graph Nodes</span>
                  <span className="text-3xl font-black text-sky-400 mt-2">
                    {knowledgeStatus?.graph?.nodes_count || 18}
                  </span>
                  <span className="text-[9px] text-slate-500 mt-1">Agricultural ontology nodes</span>
                </div>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-2xl flex flex-col justify-between">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Graph Relations</span>
                  <span className="text-3xl font-black text-indigo-400 mt-2">
                    {knowledgeStatus?.graph?.edges_count || 18}
                  </span>
                  <span className="text-[9px] text-slate-500 mt-1">Cross-domain link paths</span>
                </div>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-2xl flex flex-col justify-between">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Cache Hit Ratio</span>
                  <span className="text-3xl font-black text-teal-400 mt-2">
                    {knowledgeStatus?.health?.cache_stats ? (knowledgeStatus.health.cache_stats.hit_ratio * 100).toFixed(0) + "%" : "100%"}
                  </span>
                  <span className="text-[9px] text-slate-500 mt-1">In-memory cache efficiency</span>
                </div>
              </div>

              {/* Sub-database Health Grid */}
              <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Knowledge Source Databases Status</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { name: "Government Schemes Database", provider: "GovernmentKnowledge", desc: "PM-Kisan, PMFBY, KCC policy rules" },
                    { name: "Weather Advisories Directory", provider: "WeatherKnowledge", desc: "Climatic warnings & moisture thresholds" },
                    { name: "Market pricing Trends Index", provider: "MarketKnowledge", desc: "Historic Mandi trade summaries" },
                    { name: "Crop Agronomy Manuals", provider: "CropKnowledge", desc: "Sowing calendars & input guides" },
                    { name: "Soil Chemistry Registers", provider: "SoilKnowledge", desc: "Soil NPK profiles & pH benchmarks" },
                    { name: "Crop Disease Pathology Manuals", provider: "DiseaseKnowledge", desc: "Pathogen profiles & treatment recipes" }
                  ].map((db) => {
                    const health = knowledgeStatus?.health?.providers_health?.[db.provider.toLowerCase() + "_db"] || { status: "healthy" };
                    return (
                      <div key={db.name} className="flex items-center justify-between p-3 bg-slate-950/70 border border-slate-900 rounded-xl">
                        <div>
                          <h4 className="text-xs font-bold text-slate-200">{db.name}</h4>
                          <p className="text-[10px] text-slate-500 mt-0.5">{db.desc}</p>
                        </div>
                        <span className="text-[9px] px-2 py-0.5 rounded-full font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {health.status || "healthy"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Vector Databases Status */}
              <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Vector Database Adapters (Swappable Core)</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {[
                    { name: "FAISS", key: "faiss", desc: "Local in-memory index" },
                    { name: "ChromaDB", key: "chroma", desc: "Persistent local store" },
                    { name: "Qdrant", key: "qdrant", desc: "Cloud vector database" },
                    { name: "Pinecone", key: "pinecone", desc: "Managed cloud indices" }
                  ].map((vs) => {
                    const active = vs.key === "faiss" || vs.key === "chroma";
                    return (
                      <div key={vs.name} className="p-3.5 bg-slate-950/70 border border-slate-900 rounded-xl flex flex-col justify-between gap-2">
                        <div>
                          <h4 className="text-xs font-bold text-slate-200">{vs.name}</h4>
                          <p className="text-[9px] text-slate-500 mt-0.5">{vs.desc}</p>
                        </div>
                        <span className={`text-[9px] px-2 py-0.5 rounded-full font-mono self-start uppercase font-bold tracking-wider ${
                          active ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-slate-900 text-slate-500 border border-transparent"
                        }`}>
                          {active ? "Active Mock" : "Inactive Mock"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Knowledge Graph Traversal Paths */}
              <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Sample Explainable Graph Relations</h3>
                <div className="flex flex-col gap-2">
                  {[
                    { path: "Ramesh Singh (Farmer) --> Growing --> Wheat (Crop)", reason: "Cultivation mapping" },
                    { path: "Wheat (Crop) --> Susceptible To --> Wheat Rust (Disease)", reason: "Pathology susceptibility linking" },
                    { path: "Wheat (Crop) --> Covered By --> PMFBY (GovernmentScheme)", reason: "Insurance scheme recommendation" },
                    { path: "Wheat (Crop) --> Traded At --> Ludhiana Mandi (Market)", reason: "Economic price matching" },
                    { path: "Punjab (State) --> Spoken Language --> Punjabi (Language)", reason: "Vernacular localization routing" }
                  ].map((p, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2.5 bg-slate-950/40 border border-slate-900/60 rounded-lg">
                      <span className="text-xs font-mono text-indigo-300">{p.path}</span>
                      <span className="text-[9px] text-slate-500 uppercase tracking-wider font-bold">{p.reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 9: ANALYTICS & OPERATIONS CENTER */}
          {activeTab === "telemetry" && (
            <Suspense fallback={<div className="text-slate-500 text-sm p-8">Loading Analytics Center...</div>}>
              <AnalyticsCenter />
            </Suspense>
          )}

          {/* TAB 10: CONFIGURATION FLAGS */}
          {activeTab === "settings" && (
            <div className="flex flex-col gap-6">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <Settings className="w-5 h-5 text-emerald-400" /> Platform Configuration Toggles
              </h2>
              <p className="text-xs text-slate-400">
                Configure runtime feature flags, DI bindings, and mock gateway constraints.
              </p>

              <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-6 flex flex-col gap-4 text-xs font-semibold">
                <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-900 rounded-xl">
                  <div>
                    <h4 className="text-slate-200">Simulate LLM Provider</h4>
                    <p className="text-[10px] text-slate-500 font-normal">Use local MockLLM instead of Gemini APIs</p>
                  </div>
                  <input 
                    type="checkbox" 
                    checked={featureFlags.mockLlm} 
                    onChange={(e) => setFeatureFlags(prev => ({ ...prev, mockLlm: e.target.checked }))} 
                    className="w-4 h-4 text-emerald-500 rounded border-slate-800 bg-slate-900 focus:ring-emerald-500 focus:ring-opacity-50"
                  />
                </div>

                <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-900 rounded-xl">
                  <div>
                    <h4 className="text-slate-200">Strict Safety Scanning</h4>
                    <p className="text-[10px] text-slate-500 font-normal">Scans all voicemails and text against sensitive categories</p>
                  </div>
                  <input 
                    type="checkbox" 
                    checked={featureFlags.strictSafety} 
                    onChange={(e) => setFeatureFlags(prev => ({ ...prev, strictSafety: e.target.checked }))} 
                    className="w-4 h-4 text-emerald-500 rounded border-slate-800 bg-slate-900 focus:ring-emerald-500 focus:ring-opacity-50"
                  />
                </div>

                <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-900 rounded-xl">
                  <div>
                    <h4 className="text-slate-200">Answers Cache Toggle</h4>
                    <p className="text-[10px] text-slate-500 font-normal">Enable caching inside ARM vector indices</p>
                  </div>
                  <input 
                    type="checkbox" 
                    checked={featureFlags.cacheAnswers} 
                    onChange={(e) => setFeatureFlags(prev => ({ ...prev, cacheAnswers: e.target.checked }))} 
                    className="w-4 h-4 text-emerald-500 rounded border-slate-800 bg-slate-900 focus:ring-emerald-500 focus:ring-opacity-50"
                  />
                </div>

                <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-900 rounded-xl">
                  <div>
                    <h4 className="text-slate-200">Rate Limiting Check</h4>
                    <p className="text-[10px] text-slate-500 font-normal">Enable anti-spam query window verification</p>
                  </div>
                  <input 
                    type="checkbox" 
                    checked={featureFlags.rateLimiting} 
                    onChange={(e) => setFeatureFlags(prev => ({ ...prev, rateLimiting: e.target.checked }))} 
                    className="w-4 h-4 text-emerald-500 rounded border-slate-800 bg-slate-900 focus:ring-emerald-500 focus:ring-opacity-50"
                  />
                </div>

                <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-900 rounded-xl">
                  <div>
                    <h4 className="text-slate-200">Model Name Target</h4>
                    <p className="text-[10px] text-slate-500 font-normal">Current system model target for LLMProvider</p>
                  </div>
                  <select 
                    value={featureFlags.modelName} 
                    onChange={(e) => setFeatureFlags(prev => ({ ...prev, modelName: e.target.value }))}
                    className="bg-slate-900 text-slate-200 border border-slate-800 rounded px-2 py-1 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="mock-gemini-pro">mock-gemini-pro</option>
                    <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                    <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                  </select>
                </div>
              </div>
            </div>
          )}

        </main>
        
        <RightThinkingPanel />
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-900/60 bg-slate-950 py-3 px-6 text-center text-xs text-slate-500 flex items-center justify-between shrink-0">
        <p>&copy; 2026 Kisan Mitra AI. Open-source under Apache License 2.0.</p>
        <p className="font-semibold text-slate-400">Principal Software Engineering Team Production-Grade Platform</p>
      </footer>

    </div>
  );
}