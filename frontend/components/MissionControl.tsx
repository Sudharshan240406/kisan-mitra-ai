"use client";

import React, { useState, useEffect } from "react";
import {
  Phone,
  Mic,
  User,
  Building2,
  ClipboardCheck,
  Brain,
  BookOpen,
  TrendingUp,
  FileText,
  MapPin,
  Volume2,
  Play,
  RefreshCw,
  Zap,
  Shield,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ChevronDown,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useWebSocket, WSEvent } from "@/hooks/useWebSocket";

/* ═══════════════════════════════════════════════════════════════════════════
   Types
   ═══════════════════════════════════════════════════════════════════════════ */

interface FarmerProfile {
  farmer_id: string;
  name: string;
  phone: string;
  state: string;
  district: string;
  category: string;
  gender: string;
  land_hectares: number;
  crops: string[];
  language: string;
  caste: string;
  recent_damage: string | null;
  is_organic: boolean;
  is_tenant: boolean;
}

interface SchemeResult {
  scheme_id: string;
  title: string;
  status: string;
  confidence: number;
}

interface TranscriptLine {
  role: string;
  text: string;
  timestamp: number;
}

/* ═══════════════════════════════════════════════════════════════════════════
   Sub-components
   ═══════════════════════════════════════════════════════════════════════════ */

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    ELIGIBLE: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    POSSIBLY_ELIGIBLE: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    NEED_MORE_INFO: "bg-sky-500/20 text-sky-400 border-sky-500/30",
    NOT_ELIGIBLE: "bg-red-500/20 text-red-400 border-red-500/30",
  };
  const icons: Record<string, React.ReactNode> = {
    ELIGIBLE: <CheckCircle2 className="w-3 h-3" />,
    POSSIBLY_ELIGIBLE: <AlertCircle className="w-3 h-3" />,
    NEED_MORE_INFO: <Clock className="w-3 h-3" />,
    NOT_ELIGIBLE: <XCircle className="w-3 h-3" />,
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${colors[status] || "bg-slate-700 text-slate-300 border-slate-600"}`}>
      {icons[status]}
      {status.replace(/_/g, " ")}
    </span>
  );
}

function ConfidenceGauge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? "text-emerald-400" : pct >= 60 ? "text-amber-400" : "text-red-400";
  const bgColor = pct >= 80 ? "bg-emerald-500" : pct >= 60 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative w-20 h-20">
        <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r="34" fill="none" stroke="currentColor" strokeWidth="6" className="text-slate-800" />
          <circle cx="40" cy="40" r="34" fill="none" stroke="currentColor" strokeWidth="6" className={color}
            strokeDasharray={`${pct * 2.136} 213.6`}
            strokeLinecap="round"
            style={{ transition: "stroke-dasharray 1s ease-in-out" }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`text-lg font-black ${color}`}>{pct}%</span>
        </div>
      </div>
      <span className="text-[9px] text-slate-500 font-semibold uppercase tracking-wider">Confidence</span>
    </div>
  );
}

function PanelCard({ icon, title, badge, children, className = "" }: {
  icon: React.ReactNode;
  title: string;
  badge?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`mc-panel bg-slate-900/50 border border-slate-800/60 rounded-2xl overflow-hidden ${className}`}>
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-800/40 bg-slate-900/30">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">{title}</span>
        </div>
        {badge}
      </div>
      <div className="p-4">
        {children}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   Main Component
   ═══════════════════════════════════════════════════════════════════════════ */

export default function MissionControl() {
  // WebSocket
  const { events, lastEvent, isConnected } = useWebSocket({
    url: "ws://localhost:8000/ws/live",
  });

  // State
  const [callActive, setCallActive] = useState(false);
  const [callId, setCallId] = useState("");
  const [farmer, setFarmer] = useState<FarmerProfile | null>(null);
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [schemes, setSchemes] = useState<SchemeResult[]>([]);
  const [reasoning, setReasoning] = useState<string[]>([]);
  const [evidence, setEvidence] = useState<string[]>([]);
  const [confidence, setConfidence] = useState(0);
  const [voiceText, setVoiceText] = useState("");
  const [aiState, setAiState] = useState("IDLE");
  const [demoFarmers, setDemoFarmers] = useState<FarmerProfile[]>([]);
  const [isDemoRunning, setIsDemoRunning] = useState(false);
  const [selectedFarmer, setSelectedFarmer] = useState<string>("");
  const [elapsedMs, setElapsedMs] = useState(0);
  const [topScheme, setTopScheme] = useState<any>(null);

  // Fetch demo farmers
  useEffect(() => {
    fetch("http://localhost:8000/api/v1/demo/farmers")
      .then((r) => r.ok ? r.json() : [])
      .then(setDemoFarmers)
      .catch(() => {});
  }, []);

  // Process WebSocket events
  useEffect(() => {
    if (!lastEvent) return;
    const { type, payload } = lastEvent;

    switch (type) {
      case "CALL_STARTED":
        setCallActive(true);
        setCallId(payload.call_id || "");
        setAiState("CALL_STARTED");
        setTranscript([]);
        setSchemes([]);
        setReasoning([]);
        setEvidence([]);
        setVoiceText("");
        setConfidence(0);
        setTopScheme(null);
        break;

      case "FARMER_IDENTIFIED":
        setFarmer(payload.farmer || null);
        setAiState("FARMER_IDENTIFIED");
        break;

      case "SCHEME_MATCHING":
        setAiState("SCHEME_MATCHING");
        break;

      case "ELIGIBILITY_COMPLETE":
        setSchemes(payload.results || []);
        setAiState("ELIGIBILITY_COMPLETE");
        break;

      case "REASONING_COMPLETE":
        setReasoning(payload.reasoning || []);
        setEvidence(payload.evidence || []);
        setConfidence(payload.confidence || 0);
        setTopScheme(payload);
        setAiState("REASONING_COMPLETE");
        break;

      case "VOICE_RESPONSE_STARTED":
        setVoiceText(payload.text || "");
        setAiState("VOICE_RESPONSE");
        break;

      case "TRANSCRIPT_UPDATED":
        setTranscript((prev) => [
          ...prev,
          { role: payload.role, text: payload.text, timestamp: lastEvent.timestamp },
        ]);
        break;

      case "CALL_COMPLETED":
        setAiState("CALL_COMPLETED");
        setElapsedMs(payload.duration_ms || 0);
        setTimeout(() => setCallActive(false), 5000);
        break;

      case "DEMO_STARTED":
        setIsDemoRunning(true);
        setAiState("DEMO_RUNNING");
        break;

      case "DEMO_COMPLETED":
        setIsDemoRunning(false);
        setAiState("DEMO_COMPLETE");
        break;
    }
  }, [lastEvent]);

  // Handlers
  const handleSimulateCall = async (farmerId: string) => {
    if (!farmerId) return;
    setAiState("CONNECTING");
    try {
      await fetch(`http://localhost:8000/api/v1/demo/simulate-call/${farmerId}`, { method: "POST" });
    } catch {
      setAiState("ERROR");
    }
  };

  const handleStartDemo = async () => {
    setIsDemoRunning(true);
    try {
      await fetch("http://localhost:8000/api/v1/demo/start", { method: "POST" });
    } catch {
      setIsDemoRunning(false);
    }
  };

  const aiStateColor: Record<string, string> = {
    IDLE: "text-slate-500",
    CONNECTING: "text-sky-400",
    CALL_STARTED: "text-emerald-400",
    FARMER_IDENTIFIED: "text-teal-400",
    SCHEME_MATCHING: "text-amber-400",
    ELIGIBILITY_COMPLETE: "text-purple-400",
    REASONING_COMPLETE: "text-indigo-400",
    VOICE_RESPONSE: "text-pink-400",
    CALL_COMPLETED: "text-emerald-400",
    DEMO_RUNNING: "text-amber-400",
    DEMO_COMPLETE: "text-emerald-400",
    ERROR: "text-red-400",
  };

  return (
    <div className="flex flex-col gap-5">
      {/* Header Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-black text-slate-100 flex items-center gap-2">
            <Zap className="w-5 h-5 text-emerald-400" />
            Mission Control — Live Operations
          </h2>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Government Scheme Intelligence • Real-time IVR Dashboard
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Connection Status */}
          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-[10px] font-bold uppercase tracking-wider ${
            isConnected
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
              : "bg-red-500/10 text-red-400 border-red-500/20"
          }`}>
            {isConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
            {isConnected ? "Live Connected" : "Offline"}
          </div>

          {/* AI State */}
          <div className={`px-3 py-1.5 rounded-full border border-slate-800 text-[10px] font-bold ${aiStateColor[aiState] || "text-slate-400"}`}>
            AI: {aiState.replace(/_/g, " ")}
          </div>
        </div>
      </div>

      {/* Demo Controls */}
      <div className="mc-panel bg-gradient-to-r from-slate-900/80 to-slate-900/40 border border-slate-800/60 rounded-2xl p-4">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Phone className="w-4 h-4 text-emerald-400" />
            <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">Simulate Call</span>
          </div>

          <select
            value={selectedFarmer}
            onChange={(e) => setSelectedFarmer(e.target.value)}
            className="bg-slate-950 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-emerald-500 min-w-[220px]"
          >
            <option value="">Select a demo farmer...</option>
            {demoFarmers.map((f) => (
              <option key={f.farmer_id} value={f.farmer_id}>
                {f.name} — {f.category}, {f.district} ({f.land_hectares}ha)
              </option>
            ))}
          </select>

          <button
            onClick={() => handleSimulateCall(selectedFarmer)}
            disabled={!selectedFarmer || callActive}
            className="px-4 py-1.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 rounded-lg text-xs font-bold hover:shadow-lg hover:shadow-emerald-500/20 transition-all disabled:opacity-40 disabled:pointer-events-none flex items-center gap-1.5 cursor-pointer"
          >
            <Play className="w-3 h-3 fill-current" />
            Simulate Call
          </button>

          <div className="h-6 w-px bg-slate-800" />

          <button
            onClick={handleStartDemo}
            disabled={isDemoRunning}
            className="px-4 py-1.5 bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 rounded-lg text-xs font-bold hover:shadow-lg hover:shadow-amber-500/20 transition-all disabled:opacity-40 disabled:pointer-events-none flex items-center gap-1.5 cursor-pointer"
          >
            {isDemoRunning ? (
              <><RefreshCw className="w-3 h-3 animate-spin" /> Demo Running...</>
            ) : (
              <><Zap className="w-3 h-3" /> Full Demo (All Farmers)</>
            )}
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Column 1: Call & Transcript */}
        <div className="flex flex-col gap-4">

          {/* 📞 Live Call */}
          <PanelCard
            icon={<Phone className="w-4 h-4 text-emerald-400" />}
            title="Live Call"
            badge={callActive ? (
              <span className="mc-live-badge flex items-center gap-1 text-[9px] font-bold text-emerald-400">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                </span>
                LIVE
              </span>
            ) : null}
          >
            {callActive ? (
              <div className="flex flex-col gap-2">
                <div className="text-xs text-slate-300">
                  <span className="text-slate-500">Call ID:</span> <span className="font-mono">{callId}</span>
                </div>
                {farmer && (
                  <>
                    <div className="text-xs text-slate-300">
                      <span className="text-slate-500">Caller:</span> {farmer.name} ({farmer.phone})
                    </div>
                    <div className="text-xs text-slate-300">
                      <span className="text-slate-500">Location:</span> {farmer.district}, {farmer.state}
                    </div>
                  </>
                )}
                {elapsedMs > 0 && (
                  <div className="text-xs text-slate-400">
                    Duration: {(elapsedMs / 1000).toFixed(1)}s
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-600 italic">No active call. Select a farmer above to begin.</p>
            )}
          </PanelCard>

          {/* 🎙 Live Transcript */}
          <PanelCard
            icon={<Mic className="w-4 h-4 text-sky-400" />}
            title="Live Transcript"
            className="flex-1"
          >
            <div className="flex flex-col gap-2 max-h-[320px] overflow-y-auto pr-1 mc-scrollbar">
              {transcript.length === 0 ? (
                <p className="text-xs text-slate-600 italic">Waiting for conversation...</p>
              ) : (
                transcript.map((t, i) => (
                  <div key={i} className={`text-xs leading-relaxed rounded-lg px-3 py-2 ${
                    t.role === "farmer"
                      ? "bg-sky-500/10 border-l-2 border-sky-500/40 text-slate-200"
                      : t.role === "assistant"
                      ? "bg-emerald-500/10 border-l-2 border-emerald-500/40 text-slate-200"
                      : "bg-slate-800/40 border-l-2 border-slate-700 text-slate-400 text-[10px]"
                  }`}>
                    <span className={`font-bold uppercase text-[9px] mr-1 ${
                      t.role === "farmer" ? "text-sky-400" : t.role === "assistant" ? "text-emerald-400" : "text-slate-500"
                    }`}>
                      {t.role === "farmer" ? "👨‍🌾 Farmer" : t.role === "assistant" ? "🤖 AI" : "⚙ System"}:
                    </span>
                    {t.text}
                  </div>
                ))
              )}
            </div>
          </PanelCard>
        </div>

        {/* Column 2: Profile, Schemes, Eligibility */}
        <div className="flex flex-col gap-4">

          {/* 👤 Farmer Profile */}
          <PanelCard
            icon={<User className="w-4 h-4 text-teal-400" />}
            title="Farmer Profile"
          >
            {farmer ? (
              <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[11px]">
                <div><span className="text-slate-500">Name:</span> <span className="text-slate-200 font-semibold">{farmer.name}</span></div>
                <div><span className="text-slate-500">Category:</span> <span className="text-amber-400 font-semibold">{farmer.category}</span></div>
                <div><span className="text-slate-500">Land:</span> <span className="text-slate-200">{farmer.land_hectares} ha</span></div>
                <div><span className="text-slate-500">Gender:</span> <span className="text-slate-200">{farmer.gender}</span></div>
                <div><span className="text-slate-500">Crops:</span> <span className="text-emerald-400">{farmer.crops?.join(", ")}</span></div>
                <div><span className="text-slate-500">Caste:</span> <span className="text-slate-200">{farmer.caste}</span></div>
                <div><span className="text-slate-500">District:</span> <span className="text-slate-200">{farmer.district}</span></div>
                <div><span className="text-slate-500">State:</span> <span className="text-slate-200">{farmer.state}</span></div>
                {farmer.is_organic && <div className="col-span-2"><span className="text-green-400 font-bold">🌿 Organic Farmer</span></div>}
                {farmer.is_tenant && <div className="col-span-2"><span className="text-amber-400 font-bold">📋 Tenant Farmer</span></div>}
                {farmer.recent_damage && <div className="col-span-2"><span className="text-red-400 font-bold">⚠ Recent Damage: {farmer.recent_damage}</span></div>}
              </div>
            ) : (
              <p className="text-xs text-slate-600 italic">Farmer profile will appear when call begins.</p>
            )}
          </PanelCard>

          {/* 🏛 Scheme Search */}
          <PanelCard
            icon={<Building2 className="w-4 h-4 text-purple-400" />}
            title="Scheme Eligibility"
          >
            {schemes.length > 0 ? (
              <div className="flex flex-col gap-2 max-h-[280px] overflow-y-auto pr-1 mc-scrollbar">
                {schemes.map((s, i) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-slate-950/60 border border-slate-800/40 rounded-xl">
                    <div className="flex-1 min-w-0">
                      <p className="text-[11px] font-semibold text-slate-200 truncate">{s.title}</p>
                      <p className="text-[9px] text-slate-500 font-mono">{s.scheme_id}</p>
                    </div>
                    <div className="flex items-center gap-2 ml-2">
                      <span className="text-[10px] font-bold text-slate-400">{Math.round(s.confidence * 100)}%</span>
                      <StatusBadge status={s.status} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-600 italic">
                {aiState === "SCHEME_MATCHING" ? (
                  <span className="flex items-center gap-2 text-amber-400">
                    <RefreshCw className="w-3 h-3 animate-spin" /> Evaluating schemes...
                  </span>
                ) : "Scheme results will appear after eligibility check."}
              </p>
            )}
          </PanelCard>
        </div>

        {/* Column 3: Reasoning, Confidence, Voice */}
        <div className="flex flex-col gap-4">

          {/* 🧠 AI Reasoning */}
          <PanelCard
            icon={<Brain className="w-4 h-4 text-indigo-400" />}
            title="AI Reasoning"
          >
            {reasoning.length > 0 ? (
              <div className="flex flex-col gap-1.5 max-h-[180px] overflow-y-auto pr-1 mc-scrollbar">
                {reasoning.map((r, i) => (
                  <div key={i} className={`text-[10px] leading-relaxed px-2 py-1 rounded ${
                    r.startsWith("✓") ? "text-emerald-400 bg-emerald-500/5" :
                    r.startsWith("✗") ? "text-red-400 bg-red-500/5" :
                    r.startsWith("?") ? "text-amber-400 bg-amber-500/5" :
                    "text-slate-400"
                  }`}>
                    {r}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-600 italic">Reasoning chain will appear during evaluation.</p>
            )}
          </PanelCard>

          {/* 📈 Confidence + 📚 Evidence */}
          <div className="grid grid-cols-2 gap-4">
            <PanelCard icon={<TrendingUp className="w-4 h-4 text-amber-400" />} title="Confidence">
              <div className="flex justify-center py-2">
                <ConfidenceGauge value={confidence} />
              </div>
            </PanelCard>

            <PanelCard icon={<BookOpen className="w-4 h-4 text-cyan-400" />} title="Evidence">
              <div className="flex flex-col gap-1 max-h-[100px] overflow-y-auto mc-scrollbar">
                {evidence.length > 0 ? evidence.map((e, i) => (
                  <p key={i} className="text-[9px] text-slate-400 leading-relaxed">{e}</p>
                )) : (
                  <p className="text-[10px] text-slate-600 italic">No evidence yet.</p>
                )}
              </div>
            </PanelCard>
          </div>

          {/* 📄 Documents + 🏢 Office */}
          {topScheme && (
            <div className="grid grid-cols-1 gap-4">
              <PanelCard icon={<FileText className="w-4 h-4 text-orange-400" />} title="Documents Required">
                <p className="text-[10px] text-slate-400 mb-1">{topScheme.top_scheme}</p>
                <div className="flex flex-col gap-1">
                  {(schemes.find(s => s.status === "ELIGIBLE") ? ["Aadhaar Card", "Bank Details", "Land Records"] : []).map((d, i) => (
                    <div key={i} className="flex items-center gap-2 text-[10px]">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      <span className="text-slate-300">{d}</span>
                    </div>
                  ))}
                </div>
              </PanelCard>
            </div>
          )}

          {/* 🗣 Voice Response */}
          <PanelCard
            icon={<Volume2 className="w-4 h-4 text-pink-400" />}
            title="Voice Response"
          >
            {voiceText ? (
              <div className="bg-slate-950/60 border border-pink-500/20 rounded-xl p-3">
                <p className="text-xs text-slate-200 leading-relaxed italic">&ldquo;{voiceText}&rdquo;</p>
              </div>
            ) : (
              <p className="text-xs text-slate-600 italic">Voice response will appear here.</p>
            )}
          </PanelCard>
        </div>
      </div>

      {/* Event Timeline */}
      <PanelCard
        icon={<Clock className="w-4 h-4 text-slate-400" />}
        title="Event Timeline"
        badge={<span className="text-[9px] text-slate-500 font-mono">{events.length} events</span>}
      >
        <div className="flex gap-2 overflow-x-auto pb-2 mc-scrollbar">
          {events.slice(0, 20).map((evt, i) => (
            <div key={i} className="flex-shrink-0 px-3 py-2 bg-slate-950/60 border border-slate-800/40 rounded-xl min-w-[140px]">
              <p className="text-[9px] font-bold text-emerald-400">{evt.type}</p>
              <p className="text-[8px] text-slate-500 mt-0.5">
                {new Date(evt.timestamp * 1000).toLocaleTimeString()}
              </p>
            </div>
          ))}
          {events.length === 0 && (
            <p className="text-[10px] text-slate-600 italic">Events will stream here during calls.</p>
          )}
        </div>
      </PanelCard>
    </div>
  );
}
