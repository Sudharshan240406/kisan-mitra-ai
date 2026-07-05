"use client";

import React, { useState, useEffect, lazy, Suspense } from "react";
import dynamic from "next/dynamic";

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
  const [activeTab, setActiveTab] = useState<string>("mission-control");
  const [query, setQuery] = useState("");
  const [sessionId, setSessionId] = useState("SES-DEFAULT");
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<AdvisoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [latency, setLatency] = useState<number | null>(null);

  // Live polling data
  const [metrics, setMetrics] = useState<TelemetryMetrics | null>(null);
  const [calls, setCalls] = useState<CallSession[]>([]);
  const [smsSessions, setSmsSessions] = useState<SMSSession[]>([]);
  const [integrations, setIntegrations] = useState<any[]>([]);
  const [systemLogs, setSystemLogs] = useState<string[]>([]);
  const [alerts, setAlerts] = useState<Array<{ type: "warn" | "error" | "info"; msg: string; time: string }>>([]);
  const [knowledgeStatus, setKnowledgeStatus] = useState<any>(null);

  // AI Model Platform States
  const [aiProviders, setAiProviders] = useState<any[]>([]);
  const [aiSummary, setAiSummary] = useState<any>(null);
  const [diagPrompt, setDiagPrompt] = useState("Explain drip irrigation benefits.");
  const [diagTask, setDiagTask] = useState("advisory");
  const [diagPref, setDiagPref] = useState("");
  const [diagResponse, setDiagResponse] = useState<any>(null);
  const [diagLoading, setDiagLoading] = useState(false);
  const [newBudgetLimit, setNewBudgetLimit] = useState("5.0");

  // Feature Flags State
  const [featureFlags, setFeatureFlags] = useState({
    mockLlm: true,
    strictSafety: true,
    cacheAnswers: true,
    rateLimiting: true,
    modelName: "mock-gemini-pro"
  });

  // Agent Hub Status Check
  const [agents, setAgents] = useState<AgentHealth[]>([
    { name: "Planner Agent", role: "Intent & Graph Routing", status: "ready", latency: "2ms", icon: <Cpu className="w-4 h-4 text-emerald-400" /> },
    { name: "Weather Specialist", role: "Forecasts & Climate", status: "ready", latency: "12ms", icon: <CloudSun className="w-4 h-4 text-sky-400" /> },
    { name: "Market Specialist", role: "Pricing & Mandi Rates", status: "ready", latency: "15ms", icon: <TrendingUp className="w-4 h-4 text-amber-400" /> },
    { name: "Knowledge Specialist", role: "Pathology & Manuals", status: "ready", latency: "24ms", icon: <BookOpen className="w-4 h-4 text-indigo-400" /> },
    { name: "Scheme Matcher", role: "Welfare & Subsidies", status: "ready", latency: "18ms", icon: <Award className="w-4 h-4 text-purple-400" /> },
    { name: "Memory Specialist", role: "Conversation History & ARM", status: "ready", latency: "5ms", icon: <Database className="w-4 h-4 text-pink-400" /> },
    { name: "Verifier Agent", role: "Safety & Decision Engine", status: "ready", latency: "8ms", icon: <ShieldCheck className="w-4 h-4 text-teal-400" /> }
  ]);

  const sampleQueries = [
    "Will weather affect my wheat crop rust disease in Ludhiana Punjab?",
    "What is the mandi price of wheat and will it rain in Punjab?",
    "Will it rain today in Ludhiana?",
    "Is there any subsidy scheme for drip irrigation or crop insurance?"
  ];

  // System Health components
  const systemComponents = [
    { name: "Conversation Platform", status: "online", desc: "User session & context threads" },
    { name: "Media Intelligence", status: "online", desc: "OCR & recorded voice parsing pipelines" },
    { name: "Telephony Gateway", status: "online", desc: "BSNL/BSNL SIP trunk & Twilio interfaces" },
    { name: "SMS Gateway Service", status: "online", desc: "Feature phone alert delivery" },
    { name: "Governance & Policies", status: "online", desc: "Dynamic validator & compliance engines" },
    { name: "Execution Planner", status: "online", desc: "Topological scheduling & LangGraph compilers" },
    { name: "Event Bus Routing", status: "online", desc: "Decoupled transactional signals" }
  ];

  // Fetch metrics & active calls/SMS sessions dynamically
  const fetchLiveState = async () => {
    try {
      // 1. Telemetry metrics
      const metricsRes = await fetch(`${API_BASE}/api/v1/telemetry/metrics`);
      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }

      // 2. Active calls
      const callsRes = await fetch(`${API_BASE}/api/v1/telephony/calls`);
      if (callsRes.ok) {
        const callsData = await callsRes.json();
        setCalls(callsData);
      }

      // 3. SMS Sessions
      const smsRes = await fetch(`${API_BASE}/api/v1/sms/sessions`);
      if (smsRes.ok) {
        const smsData = await smsRes.json();
        setSmsSessions(smsData);
      }

      // 4. Integrations Platform
      const integrationsRes = await fetch(`${API_BASE}/api/v1/integrations`);
      if (integrationsRes.ok) {
        const integrationsData = await integrationsRes.json();
        setIntegrations(integrationsData);
      }

      // 5. AI Platform Providers specifications
      const aiProvidersRes = await fetch(`${API_BASE}/api/v1/ai/providers`);
      if (aiProvidersRes.ok) {
        const aiProvidersData = await aiProvidersRes.json();
        setAiProviders(aiProvidersData);
      }

      // 6. AI Platform budget summary logs
      const aiSummaryRes = await fetch(`${API_BASE}/api/v1/ai/summary`);
      if (aiSummaryRes.ok) {
        const aiSummaryData = await aiSummaryRes.json();
        setAiSummary(aiSummaryData);
      }

      // 7. Knowledge Platform status
      const knowledgeRes = await fetch(`${API_BASE}/api/v1/knowledge/status`);
      if (knowledgeRes.ok) {
        const knowledgeData = await knowledgeRes.json();
        setKnowledgeStatus(knowledgeData);
      }
    } catch (e) {
      console.log("Telemetry fetch skipped - backend may be offline.", e);
    }
  };

  useEffect(() => {
    fetchLiveState();
    const interval = setInterval(fetchLiveState, 4000);
    return () => clearInterval(interval);
  }, []);

  // Sync state log additions
  const logEvent = (msg: string, type: "info" | "warn" | "error" = "info") => {
    const timestamp = new Date().toLocaleTimeString();
    setSystemLogs(prev => [`[${timestamp}] ${msg}`, ...prev.slice(0, 49)]);
    setAlerts(prev => [{ type, msg, time: timestamp }, ...prev.slice(0, 19)]);
  };

  const handleQuerySubmit = async (queryText: string) => {
    if (!queryText.trim()) return;
    setIsLoading(true);
    setError(null);
    setResponse(null);
    setLatency(null);
    logEvent(`Initiating LangGraph multi-agent compile for query: "${queryText.slice(0, 30)}..."`, "info");
    
    setAgents(prev => prev.map(a => ({ ...a, status: "running" })));
    const startTime = performance.now();

    try {
      const res = await fetch(`${API_BASE}/api/v1/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: queryText, session_id: sessionId })
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status} ${res.statusText}`);
      }

      const data = await res.json();
      if (data.status === "success") {
        setResponse(data.data);
        logEvent(`Successfully generated trusted advisory (Confidence: ${(data.data.confidence * 100).toFixed(0)}%)`, "info");
        
        // Add alerts if risk score is high
        if (data.data.risk > 0.4) {
          logEvent(`Elevated risk detected on query advice! (Score: ${(data.data.risk * 100).toFixed(0)}%)`, "warn");
        }
      } else {
        throw new Error(data.message || "Failed to generate advisory.");
      }
    } catch (err: any) {
      console.error(err);
      const errMsg = err.message || "Pipeline execution failed. Ensure backend server is running.";
      setError(errMsg);
      logEvent(`Query compile error: ${errMsg}`, "error");
    } finally {
      setIsLoading(false);
      const endTime = performance.now();
      setLatency(Math.round(endTime - startTime));
      setAgents(prev => prev.map(a => ({ ...a, status: "ready" })));
      fetchLiveState();
    }
  };

  const cleanExpiredSessions = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/channels/sessions/cleanup`, { method: "POST" });
      if (res.ok) {
        logEvent("Manually triggered expired communication sessions cleanup", "info");
      }
    } catch (e) {
      logEvent("Failed to trigger manual sessions cleanup", "error");
    }
  };

  const handleToggleIntegration = async (integrationId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/integrations/${integrationId}/toggle`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        logEvent(`Successfully toggled integration ${integrationId} status to ${data.new_status}`, "info");
        fetchLiveState();
      } else {
        logEvent(`Failed to toggle integration ${integrationId}`, "error");
      }
    } catch (e) {
      logEvent(`Failed to toggle integration ${integrationId}: connection error`, "error");
    }
  };

  const handleActivateIntegration = async (integrationId: string, type: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/integrations/${integrationId}/activate`, { method: "POST" });
      if (res.ok) {
        logEvent(`Activated integration ${integrationId} as active provider for ${type}`, "info");
        fetchLiveState();
      } else {
        logEvent(`Failed to activate integration ${integrationId}`, "error");
      }
    } catch (e) {
      logEvent(`Failed to activate integration ${integrationId}: connection error`, "error");
    }
  };

  const handleTestIntegration = async (integrationId: string) => {
    try {
      logEvent(`Executing test run for integration adapter: ${integrationId}...`, "info");
      const res = await fetch(`${API_BASE}/api/v1/integrations/${integrationId}/test`, { method: "POST" });
      const data = await res.json();
      if (data.status === "success") {
        logEvent(`Integration ${integrationId} test completed successfully. Result: ${data.result}`, "info");
        fetchLiveState();
      } else {
        logEvent(`Integration ${integrationId} test failed: ${data.error}`, "error");
      }
    } catch (e) {
      logEvent(`Integration ${integrationId} test failed: connection error`, "error");
    }
  };


  // Pre-compiled fallback metric statistics
  const fallbackMetrics: TelemetryMetrics = {
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

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans select-none selection:bg-emerald-500 selection:text-slate-950">
      
      {/* Top Navigation Header */}
      <header className="border-b border-slate-900 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Cpu className="w-5 h-5 text-slate-950 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-teal-200">
              KISAN MITRA COMMAND CENTER
            </h1>
            <p className="text-xs text-slate-400 font-medium">Operations Control Center & Platform Monitor v1.0</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 bg-slate-900/60 px-3 py-1.5 rounded-full border border-slate-800">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Advisory Platform: Baseline 1.0</span>
          </div>

          <div className="text-xs text-slate-400">
            Current Session: <strong className="text-slate-200">{sessionId}</strong>
          </div>
        </div>
      </header>

      {/* Main Core Layout Grid */}
      <div className="flex-1 max-w-8xl w-full mx-auto p-6 flex flex-col md:flex-row gap-6">
        
        {/* Left Side Navigation Panels */}
        <aside className="w-full md:w-64 bg-slate-900/40 border border-slate-900 rounded-2xl p-5 flex flex-col gap-2">
          <div className="flex items-center gap-2 border-b border-slate-900 pb-3 mb-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <span className="font-bold text-slate-200 text-xs uppercase tracking-wider">Navigations Modules</span>
          </div>

          <nav className="flex flex-col gap-1.5">
            {[
              { id: "mission-control", label: "⚡ Mission Control", icon: <Radio className="w-4 h-4" /> },
              { id: "overview", label: "Overview", icon: <Server className="w-4 h-4" /> },
              { id: "platform", label: "Agent Playground", icon: <MessageSquare className="w-4 h-4" /> },
              { id: "ai", label: "AI Specialist Hub", icon: <Cpu className="w-4 h-4" /> },
              { id: "conversations", label: "Conversations Monitor", icon: <List className="w-4 h-4" /> },
              { id: "media", label: "Media Ingestion", icon: <HardDrive className="w-4 h-4" /> },
              { id: "telephony", label: "Telephony & IVR", icon: <Phone className="w-4 h-4" /> },
              { id: "sms", label: "SMS Gateway", icon: <Mail className="w-4 h-4" /> },
              { id: "governance", label: "Governance & Registry", icon: <ShieldCheck className="w-4 h-4" /> },
              { id: "integrations", label: "Integrations Platform", icon: <RefreshCw className="w-4 h-4" /> },
              { id: "knowledge", label: "Knowledge Platform", icon: <BookOpen className="w-4 h-4" /> },
              { id: "telemetry", label: "Telemetry & Logs", icon: <Terminal className="w-4 h-4" /> },
              { id: "settings", label: "Configuration Flags", icon: <Settings className="w-4 h-4" /> }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-left text-xs font-semibold tracking-wide transition-all ${
                  activeTab === tab.id
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent"
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </nav>

          <div className="mt-8 border-t border-slate-900 pt-4">
            <div className="flex items-center gap-2 mb-2">
              <Bell className="w-4 h-4 text-amber-400" />
              <span className="font-bold text-slate-400 text-[10px] uppercase tracking-wider">Recent Alerts Stream</span>
            </div>
            <div className="flex flex-col gap-1.5 max-h-36 overflow-y-auto pr-1">
              {alerts.length === 0 ? (
                <span className="text-[10px] text-slate-600">No alerts logged.</span>
              ) : (
                alerts.map((alert, i) => (
                  <div key={i} className="text-[9px] leading-relaxed border-l-2 border-slate-800 pl-2 py-0.5">
                    <span className={`font-bold uppercase ${
                      alert.type === "error" ? "text-red-400" : alert.type === "warn" ? "text-amber-400" : "text-sky-400"
                    }`}>{alert.type}:</span> {alert.msg}
                  </div>
                ))
              )}
            </div>
          </div>
        </aside>

        {/* Dynamic Display Panel */}
        <main className="flex-1 bg-slate-900/20 border border-slate-900 rounded-3xl p-6 overflow-y-auto">
          
          {/* TAB 0: MISSION CONTROL */}
          {activeTab === "mission-control" && (
            <Suspense fallback={<div className="text-slate-500 text-sm p-8">Loading Mission Control...</div>}>
              <MissionControl />
            </Suspense>
          )}

          {/* TAB 1: OVERVIEW */}
          {activeTab === "overview" && (
            <div className="flex flex-col gap-6">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <Server className="w-5 h-5 text-emerald-400" /> Operations Overview
              </h2>

              {/* Status metrics grid */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-2xl flex flex-col justify-between">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Processed Messages</span>
                  <span className="text-3xl font-black text-emerald-400 mt-2">{activeMetrics.channel_metrics.messages_processed + activeMetrics.sms_metrics.received_count}</span>
                  <span className="text-[9px] text-slate-500 mt-1">Omnichannel & SMS total</span>
                </div>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-2xl flex flex-col justify-between">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Avg Latency</span>
                  <span className="text-3xl font-black text-sky-400 mt-2">{(activeMetrics.workflow_latency.avg_ms).toFixed(1)} ms</span>
                  <span className="text-[9px] text-slate-500 mt-1">Worker compilation & scheduling</span>
                </div>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-2xl flex flex-col justify-between">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Active Telephony Calls</span>
                  <span className="text-3xl font-black text-indigo-400 mt-2">{calls.filter(c => c.status !== "completed").length}</span>
                  <span className="text-[9px] text-slate-500 mt-1">Live IVR navigation sessions</span>
                </div>
                <div className="bg-slate-900/40 border border-slate-850 p-4 rounded-2xl flex flex-col justify-between">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">SMS Delivery Rate</span>
                  <span className="text-3xl font-black text-teal-400 mt-2">{(activeMetrics.sms_metrics.delivery_rate * 100).toFixed(0)}%</span>
                  <span className="text-[9px] text-slate-500 mt-1">Total success/fail ratio</span>
                </div>
              </div>

              {/* Subsystems Health */}
              <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Core Platform Subsystems Health</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {systemComponents.map((c) => (
                    <div key={c.name} className="flex items-center justify-between p-3 bg-slate-950/70 border border-slate-900 rounded-xl">
                      <div>
                        <h4 className="text-xs font-bold text-slate-200">{c.name}</h4>
                        <p className="text-[10px] text-slate-500 mt-0.5">{c.desc}</p>
                      </div>
                      <span className="text-[9px] px-2 py-0.5 rounded-full font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {c.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Live Metric Graphs */}
              <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-5">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Live Performance Telemetry</h3>
                <div className="h-44 w-full flex items-end gap-1 px-4 border-b border-l border-slate-800 pb-2">
                  {[12, 18, 15, 24, 30, 20, 16, 28, 35, 45, 12, 10, 24, 30, 28, 48, 55, 62, 40, 30].map((val, idx) => (
                    <div 
                      key={idx} 
                      className="bg-emerald-500/80 hover:bg-emerald-400 w-full transition-all duration-300 rounded-t-sm" 
                      style={{ height: `${val * 2}%` }}
                      title={`Time point: ${idx}, Value: ${val}`}
                    />
                  ))}
                </div>
                <div className="flex justify-between text-[9px] text-slate-500 mt-2 px-1">
                  <span>-60 seconds</span>
                  <span>Active Query Resolution Latency</span>
                  <span>Now</span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: AGENT PLAYGROUND */}
          {activeTab === "platform" && (
            <div className="flex flex-col gap-6">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-emerald-400" /> Agronomic Advisory Request Playground
              </h2>

              <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-6 flex flex-col gap-4">
                <p className="text-xs text-slate-400 leading-relaxed">
                  Type or click seed queries below to compile execution paths, run safety rules validations, and audit metrics.
                </p>

                <div className="relative">
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask an agricultural query..."
                    rows={3}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder:text-slate-650 focus:outline-none focus:border-emerald-500/70 focus:ring-1 focus:ring-emerald-500/30 transition-all resize-none"
                  />
                  <button
                    onClick={() => handleQuerySubmit(query)}
                    disabled={isLoading || !query.trim()}
                    className="absolute right-3.5 bottom-3.5 px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 rounded-lg text-xs font-bold hover:shadow-lg hover:shadow-emerald-500/20 transition-all duration-300 disabled:opacity-50 disabled:pointer-events-none flex items-center gap-1.5 cursor-pointer"
                  >
                    {isLoading ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        Executing LangGraph...
                      </>
                    ) : (
                      <>
                        <Play className="w-3 h-3 fill-current" />
                        Execute Ingress
                      </>
                    )}
                  </button>
                </div>

                <div className="flex flex-col gap-2">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Quick Seeds:</span>
                  <div className="flex flex-wrap gap-2">
                    {sampleQueries.map((q) => (
                      <button
                        key={q}
                        onClick={() => {
                          setQuery(q);
                          handleQuerySubmit(q);
                        }}
                        disabled={isLoading}
                        className="px-3 py-1.5 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg text-xs text-slate-300 text-left transition duration-200 cursor-pointer disabled:opacity-50"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Advisory Response Display */}
              {isLoading && (
                <div className="bg-slate-900/30 border border-slate-900 rounded-2xl p-8 flex flex-col items-center justify-center gap-4 text-center">
                  <div className="w-10 h-10 rounded-full border-t-2 border-emerald-500 animate-spin"></div>
                  <span className="text-xs text-slate-200">Executing Node Compilation & Safety Policy scan...</span>
                </div>
              )}

              {error && (
                <div className="bg-red-950/20 border border-red-900/30 rounded-2xl p-4 text-xs text-red-300">
                  {error}
                </div>
              )}

              {response && (
                <div className="flex flex-col gap-6">
                  {/* Confidence and Risk Info */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-slate-900/40 border border-slate-800 p-4 rounded-xl">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Confidence Level</span>
                      <p className="text-2xl font-black text-emerald-400 mt-1">{(response.confidence * 100).toFixed(0)}%</p>
                    </div>
                    <div className="bg-slate-900/40 border border-slate-800 p-4 rounded-xl">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Policy Risk Assessed</span>
                      <p className="text-2xl font-black text-amber-500 mt-1">{(response.risk * 100).toFixed(0)}%</p>
                    </div>
                    <div className="bg-slate-900/40 border border-slate-800 p-4 rounded-xl">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Total Check Latency</span>
                      <p className="text-2xl font-black text-sky-400 mt-1">{latency} ms</p>
                    </div>
                  </div>

                  {/* Recommendation Content */}
                  <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5">
                    <h4 className="font-bold text-slate-200 text-xs uppercase tracking-wider border-b border-slate-900 pb-2 mb-3">Recommendation output</h4>
                    <p className="text-xs font-semibold text-emerald-400 mb-2">{response.summary}</p>
                    <p className="text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-line">{response.recommendation}</p>
                  </div>

                  {/* Evidence List */}
                  <div className="flex flex-col gap-3">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Consolidated Evidence Items</span>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {response.evidence.map((ev, i) => (
                        <div key={i} className="p-3 bg-slate-950/60 border border-slate-900 rounded-xl">
                          <div className="flex justify-between items-center text-[10px] font-bold text-slate-400 mb-2">
                            <span>{ev.agent} agent</span>
                            <span className="text-emerald-400">{(ev.confidence * 100).toFixed(0)}%</span>
                          </div>
                          <p className="text-xs text-slate-300">"{ev.reasoning}"</p>
                          <p className="text-[9px] text-slate-500 mt-2">Source: {ev.source}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
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

          {/* TAB 9: TELEMETRY & LOGS */}
          {activeTab === "telemetry" && (
            <div className="flex flex-col gap-6">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <Terminal className="w-5 h-5 text-emerald-400" /> Live Platform Logs Console
              </h2>
              <p className="text-xs text-slate-400">
                Audits trace loops, graph compilers, and active API response transactions.
              </p>

              <div className="bg-slate-950 border border-slate-900 rounded-2xl p-5 font-mono text-[11px] leading-relaxed text-slate-300 h-96 overflow-y-auto flex flex-col-reverse gap-2">
                {systemLogs.length === 0 ? (
                  <span className="text-slate-600">Console listening. Execute query to see logs stream...</span>
                ) : (
                  systemLogs.map((log, idx) => (
                    <div key={idx} className="border-b border-slate-900 pb-1.5">
                      {log}
                    </div>
                  ))
                )}
              </div>
            </div>
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
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 px-6 mt-12 text-center text-xs text-slate-500 flex items-center justify-between">
        <p>&copy; 2026 Kisan Mitra AI. Open-source under Apache License 2.0.</p>
        <p className="font-semibold text-slate-400">Principal Software Engineering Team Production-Grade Platform</p>
      </footer>

    </div>
  );
}
