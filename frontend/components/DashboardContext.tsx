"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { Cpu, CloudSun, TrendingUp, BookOpen, Award, Database, ShieldCheck } from "lucide-react";
import { useWebSocket, WSEvent } from "@/hooks/useWebSocket";

export interface EvidenceItem {
  id: string;
  source: string;
  agent: string;
  confidence: number;
  weight: number;
  reasoning: string;
  citation?: string;
}

export interface AdvisoryResponse {
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

export interface AgentHealth {
  name: string;
  role: string;
  status: "idle" | "running" | "ready" | "offline";
  latency: string;
  icon: React.ReactNode;
}

export interface TelemetryMetrics {
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

export interface CallSession {
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

export interface SMSSession {
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

export interface SystemAlert {
  type: "warn" | "error" | "info";
  msg: string;
  time: string;
}

interface DashboardContextType {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  query: string;
  setQuery: (q: string) => void;
  sessionId: string;
  setSessionId: (id: string) => void;
  isLoading: boolean;
  setIsLoading: (val: boolean) => void;
  response: AdvisoryResponse | null;
  setResponse: (res: AdvisoryResponse | null) => void;
  error: string | null;
  setError: (err: string | null) => void;
  latency: number | null;
  setLatency: (lat: number | null) => void;
  metrics: TelemetryMetrics | null;
  calls: CallSession[];
  smsSessions: SMSSession[];
  integrations: any[];
  systemLogs: string[];
  alerts: SystemAlert[];
  knowledgeStatus: any;
  aiProviders: any[];
  aiSummary: any;
  diagPrompt: string;
  setDiagPrompt: (q: string) => void;
  diagTask: string;
  setDiagTask: (task: string) => void;
  diagPref: string;
  setDiagPref: (pref: string) => void;
  diagResponse: any;
  setDiagResponse: (res: any) => void;
  diagLoading: boolean;
  setDiagLoading: (val: boolean) => void;
  newBudgetLimit: string;
  setNewBudgetLimit: (limit: string) => void;
  featureFlags: {
    mockLlm: boolean;
    strictSafety: boolean;
    cacheAnswers: boolean;
    rateLimiting: boolean;
    modelName: string;
  };
  setFeatureFlags: React.Dispatch<React.SetStateAction<{
    mockLlm: boolean;
    strictSafety: boolean;
    cacheAnswers: boolean;
    rateLimiting: boolean;
    modelName: string;
  }>>;
  agents: AgentHealth[];
  setAgents: React.Dispatch<React.SetStateAction<AgentHealth[]>>;
  sampleQueries: string[];
  systemComponents: Array<{ name: string; status: string; desc: string }>;
  fetchLiveState: () => Promise<void>;
  logEvent: (msg: string, type?: "info" | "warn" | "error") => void;
  handleQuerySubmit: (queryText: string) => Promise<void>;
  cleanExpiredSessions: () => Promise<void>;
  handleToggleIntegration: (integrationId: string) => Promise<void>;
  handleActivateIntegration: (integrationId: string, type: string) => Promise<void>;
  handleTestIntegration: (integrationId: string) => Promise<void>;
  updateBudgetLimit: (limit: number) => Promise<void>;
  toggleModelAvailability: (modelId: string, nextState: string) => Promise<void>;
  runRouterDiagnostic: () => Promise<void>;

  // WebSocket shared state
  lastEvent: WSEvent | null;
  isConnected: boolean;
  clientCount: number;
  reconnectCount: number;
  aiState: string;
  setAiState: (state: string) => void;
  callActive: boolean;
  setCallActive: (active: boolean) => void;
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

import { getApiBase, getWsBase } from "@/lib/utils";

const API_BASE = getApiBase();
const WS_BASE = getWsBase();

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [activeTab, setActiveTab] = useState<string>("overview");
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
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
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

  // Shared workflow and call simulation states derived from WS
  const [aiState, setAiState] = useState("READY");
  const [callActive, setCallActive] = useState(false);

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

  const logEvent = useCallback((msg: string, type: "info" | "warn" | "error" = "info") => {
    const timestamp = new Date().toLocaleTimeString();
    setSystemLogs(prev => [`[${timestamp}] ${msg}`, ...prev.slice(0, 49)]);
    setAlerts(prev => [{ type, msg, time: timestamp }, ...prev.slice(0, 19)]);
  }, []);

  // Shared WebSocket hook
  const { lastEvent, isConnected, clientCount, reconnectCount } = useWebSocket({
    url: `${WS_BASE}/ws/live`,
  });

  // Track call and simulation stages from WebSocket events
  useEffect(() => {
    if (!lastEvent) return;
    const { type, payload } = lastEvent;

    switch (type) {
      case "CALL_STARTED":
        setCallActive(true);
        setAiState("CALL_STARTED");
        logEvent(`Simulation call active: ${payload.call_id}`, "info");
        break;
      case "CALLER_IDENTIFIED":
        setAiState("CALLER_IDENTIFIED");
        logEvent(`Farmer identified: ${payload.farmer_name} (${payload.phone})`, "info");
        break;
      case "DIGITAL_TWIN_LOADED":
        setAiState("DIGITAL_TWIN_LOADED");
        logEvent(`Digital twin compiled successfully`, "info");
        break;
      case "SCHEME_SEARCH_STARTED":
        setAiState("SCHEME_SEARCH_STARTED");
        break;
      case "SCHEME_MATCHED":
        setAiState("SCHEME_EVALUATING");
        break;
      case "ELIGIBILITY_COMPLETED":
        setAiState("ELIGIBILITY_COMPLETED");
        break;
      case "REASONING_COMPLETED":
        setAiState("REASONING_COMPLETED");
        logEvent(`Advisory reasoning completed for: ${payload.top_scheme}`, "info");
        break;
      case "DOCUMENT_ADVISOR_READY":
        setAiState("DOCUMENT_ADVISOR_READY");
        break;
      case "VOICE_RESPONSE_STARTED":
        setAiState("VOICE_RESPONSE");
        break;
      case "CALL_COMPLETED":
        setAiState("CALL_COMPLETED");
        logEvent(`Simulation call completed. Duration: ${(payload.duration_ms / 1000).toFixed(1)}s`, "info");
        setTimeout(() => setCallActive(false), 8000);
        break;
      case "CALL_ERROR":
        setAiState("ERROR");
        logEvent(`Simulation call failed: ${payload.error}`, "error");
        break;
      case "ERROR_RECOVERY_STARTED":
        setAiState("ERROR_RECOVERY");
        break;
    }
  }, [lastEvent, logEvent]);

  const fetchLiveState = useCallback(async () => {
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
  }, []);

  useEffect(() => {
    fetchLiveState();
    const interval = setInterval(fetchLiveState, 4000);
    return () => clearInterval(interval);
  }, [fetchLiveState]);

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

  const updateBudgetLimit = async (limit: number) => {
    try {
      await fetch(`${API_BASE}/api/v1/ai/budget`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ daily_budget_usd: limit })
      });
      logEvent(`Daily AI budget limit successfully updated to $${limit.toFixed(2)}`, "info");
      fetchLiveState();
    } catch (e) {
      logEvent("Failed to update AI daily budget limit", "error");
    }
  };

  const toggleModelAvailability = async (modelId: string, nextState: string) => {
    try {
      await fetch(`${API_BASE}/api/v1/ai/toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_id: modelId, availability: nextState })
      });
      logEvent(`Toggled model '${modelId}' availability state to '${nextState}'`, "info");
      fetchLiveState();
    } catch (e) {
      logEvent("Failed to toggle model availability", "error");
    }
  };

  const runRouterDiagnostic = async () => {
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
  };

  return (
    <DashboardContext.Provider value={{
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
      updateBudgetLimit, toggleModelAvailability, runRouterDiagnostic,
      
      // WS shared details
      lastEvent, isConnected, clientCount, reconnectCount,
      aiState, setAiState,
      callActive, setCallActive
    }}>
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboard must be used within a DashboardProvider");
  }
  return context;
}
