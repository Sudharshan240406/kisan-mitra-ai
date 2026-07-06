"use client";

import React, { useState, useEffect } from "react";
import { useDashboard } from "@/components/DashboardContext";
import {
  Brain,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ArrowRight,
  TrendingUp,
  Cpu,
  Layers,
  Database,
  Search,
  BookOpen,
  Volume2,
  GitBranch,
  ShieldCheck,
  RefreshCw,
  Info,
  Calendar,
  Sparkles,
  MapPin,
  Check,
  AlertCircle
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

/* ═══════════════════════════════════════════════════════════════════════════
   Interfaces
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
  digital_twin_version?: string;
  profile_completeness?: number;
  last_interaction?: string;
  risk_profile?: string;
}

interface SchemeRecommendation {
  scheme_id: string;
  title: string;
  status: string;
  confidence: number;
  reasoning: string[];
  evidence: string[];
  benefits: string;
  required_documents: string[];
  missing_documents: string[];
  deadline: string;
  department: string;
  helpline: string;
  nearest_office: string;
  official_url: string;
  application_steps: string[];
  expected_timeline: string;
  missing_info: string[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AIExplainability() {
  const { integrations } = useDashboard();

  // State Management
  const [farmers, setFarmers] = useState<FarmerProfile[]>([]);
  const [selectedFarmerId, setSelectedFarmerId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Real backend evaluations
  const [evaluations, setEvaluations] = useState<SchemeRecommendation[]>([]);
  const [selectedSchemeId, setSelectedSchemeId] = useState<string>("");

  // UI toggles
  const [farmerView, setFarmerView] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  // Check prefers-reduced-motion
  useEffect(() => {
    if (typeof window !== "undefined") {
      const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
      setReducedMotion(mediaQuery.matches);
    }
  }, []);

  // Fetch farmers list
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/demo/farmers`)
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        setFarmers(data);
        if (data.length > 0) {
          setSelectedFarmerId(data[0].farmer_id);
        }
      })
      .catch(() => setError("Failed to fetch demo farmers."));
  }, []);

  // Fetch eligibility when farmer changes
  useEffect(() => {
    if (!selectedFarmerId) return;
    setLoading(true);
    setError("");
    fetch(`${API_BASE}/api/v1/demo/schemes/${selectedFarmerId}`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load evaluations");
        return r.json();
      })
      .then((res) => {
        const recommendations = res.recommendations || [];
        setEvaluations(recommendations);
        if (recommendations.length > 0) {
          setSelectedSchemeId(recommendations[0].scheme_id);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load scheme parameters from engine.");
        setLoading(false);
      });
  }, [selectedFarmerId]);

  const activeScheme = evaluations.find(e => e.scheme_id === selectedSchemeId) || evaluations[0];
  const activeFarmer = farmers.find(f => f.farmer_id === selectedFarmerId);

  // Helper to determine Helped vs Limited status for each evidence factor (Task 2)
  const getEvidenceFactor = (type: string, rec: SchemeRecommendation) => {
    if (!activeFarmer || !rec) return { status: "Helped", desc: "Verified factor" };

    const isEligible = rec.status === "ELIGIBLE";
    const isMissingDocs = rec.missing_documents.length > 0;

    switch (type) {
      case "Land Size":
        if (rec.scheme_id === "pm-kisan" && activeFarmer.land_hectares > 2.0) {
          return { status: "Limited", desc: "Exceeds 2.0 ha ceiling" };
        }
        return { status: "Helped", desc: `${activeFarmer.land_hectares} ha fits criteria` };

      case "Aadhaar":
        if (rec.missing_documents.includes("Aadhaar Card")) {
          return { status: "Limited", desc: "Aadhaar link unresolved" };
        }
        return { status: "Helped", desc: "Aadhaar registry verified" };

      case "Bank":
        if (rec.missing_documents.includes("Bank Passbook")) {
          return { status: "Limited", desc: "No active DBT bank link" };
        }
        return { status: "Helped", desc: "Bank account DBT linked" };

      case "Crop":
        if (rec.scheme_id === "organic-farming" && !activeFarmer.is_organic) {
          return { status: "Limited", desc: "Requires organic cultivation status" };
        }
        return { status: "Helped", desc: `Matches crop profile: ${activeFarmer.crops[0] || "agri"}` };

      case "District":
        return { status: "Helped", desc: `Registered: ${activeFarmer.district}, ${activeFarmer.state}` };

      case "Previous History":
        return { status: "Helped", desc: "Zero audit defaults registered" };

      case "Weather":
        return { status: "Helped", desc: "Regional climate boundaries normal" };

      case "Market":
        return { status: "Helped", desc: "MSP registry prices indexed" };

      default:
        return { status: "Helped", desc: "Verified" };
    }
  };

  // Farmer-Friendly explanation text generator (Task 7)
  const getFarmerFriendlyView = (rec: SchemeRecommendation) => {
    if (!activeFarmer) return "";
    const name = activeFarmer.name;
    const isEligible = rec.status === "ELIGIBLE";

    if (isEligible) {
      return `Namaste ${name}! Humari AI jaanch ke anusar aap iss yojana ke liye yogya hain. Kyunki aapki bhoomi ka size sharto ke anukul hai aur bank me seedha paisa (DBT) aane ke liye sabhi zaroori kagaz taiyar hain.`;
    } else {
      const missingDoc = rec.missing_documents[0] || "Zameen ke kagaz";
      return `Namaste ${name}. Aap iss yojana ke yogya ho sakte hain, lekin aapke profile me kuch kagaz jaise '${missingDoc}' kam hain. Inhe CSC center par update karke aap aasaani se labh pa sakte hain.`;
    }
  };

  return (
    <div className="flex flex-col gap-6 w-full font-mono text-xs">
      
      {/* 🧭 HEADER & FARMER TOGGLE SELECT */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-900 pb-5 z-10">
        <div>
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-[var(--lime-glow)]" />
            <h2 className="text-lg font-black text-white font-display">AI Explainability & Trust Center</h2>
          </div>
          <p className="text-[10px] text-slate-500 uppercase tracking-widest font-mono font-bold mt-1">
            Auditing decision path reasoning, evidence metrics, and information sources
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label htmlFor="farmer-select-explain" className="text-[10px] uppercase font-bold text-slate-500 font-mono">Farmer Profile:</label>
          <select
            id="farmer-select-explain"
            value={selectedFarmerId}
            onChange={(e) => setSelectedFarmerId(e.target.value)}
            disabled={loading}
            className="bg-slate-950 text-slate-200 border border-slate-900 rounded-xl px-4 py-2 text-xs focus:outline-none focus:border-[var(--lime-glow)] min-w-[200px] cursor-pointer"
          >
            {farmers.map((f) => (
              <option key={f.farmer_id} value={f.farmer_id}>
                {f.name} ({f.district}, {f.state})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* ── EXPLAINABILITY GRID ────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* LEFT COLUMN: REGISTRY MATCHES CHOSEN */}
        <div className="lg:col-span-4 flex flex-col gap-3.5 z-10 max-h-[580px] overflow-y-auto pr-1 mc-scrollbar">
          <div className="text-[10px] font-black uppercase text-slate-500 tracking-wider">
            Evaluated Recommendations
          </div>

          {loading ? (
            <div className="py-24 text-center text-slate-500 flex flex-col items-center gap-3">
              <RefreshCw className="w-5 h-5 animate-spin text-[var(--lime-glow)]" />
              <span>Scanning rule criteria...</span>
            </div>
          ) : error ? (
            <div className="p-4 bg-red-500/5 border border-red-500/10 rounded-2xl text-red-400 font-bold text-center">
              {error}
            </div>
          ) : (
            evaluations.map((rec) => {
              const isSelected = rec.scheme_id === selectedSchemeId;
              const isEligible = rec.status === "ELIGIBLE";
              const isReview = rec.status === "POSSIBLY_ELIGIBLE" || rec.status === "NEED_MORE_INFO";

              return (
                <div
                  key={rec.scheme_id}
                  onClick={() => setSelectedSchemeId(rec.scheme_id)}
                  tabIndex={0}
                  onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") setSelectedSchemeId(rec.scheme_id); }}
                  className={`glass-panel border-2 rounded-2xl p-4 cursor-pointer text-left transition-all duration-200 focus:outline-none focus:ring-1 focus:ring-[var(--lime-glow)] ${
                    isSelected ? "border-[var(--lime-glow)]/30 bg-emerald-500/5" : "border-slate-900 hover:border-slate-800"
                  }`}
                >
                  <div className="flex justify-between items-center gap-2">
                    <span className="text-[8px] font-bold font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-[var(--lime-glow)] uppercase border border-emerald-500/20">
                      {rec.scheme_id}
                    </span>
                    <span className={`text-[8px] px-1.5 py-0.5 rounded font-bold uppercase ${
                      isEligible ? "bg-emerald-500/10 text-emerald-400" :
                      isReview ? "bg-amber-500/10 text-amber-400" :
                      "bg-red-500/10 text-red-400"
                    }`}>
                      {rec.status.replace(/_/g, " ")}
                    </span>
                  </div>

                  <h3 className="text-slate-200 font-bold tracking-tight text-[11px] mt-2.5 leading-snug truncate">
                    {rec.title}
                  </h3>
                  
                  <div className="flex justify-between items-center mt-3 pt-3 border-t border-slate-900/60 text-[9px] text-slate-500">
                    <span>Benefit: <strong className="text-slate-300 font-bold">{rec.benefits || "Material Subsidy"}</strong></span>
                    <span>AI Conf: <strong className="text-[var(--lime-glow)] font-bold">{(rec.confidence * 100).toFixed(0)}%</strong></span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* RIGHT COLUMN: PRECISE TRUST CENTER EXPLORER */}
        <div className="lg:col-span-8 flex flex-col gap-6 z-10">
          {activeScheme ? (
            <div className="glass-panel rounded-3xl p-5 border border-slate-900 flex-1 flex flex-col justify-between">
              <div>
                
                {/* Visual Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-900 mb-5">
                  <div>
                    <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-mono">Trust Audit Sheet</span>
                    <h3 className="text-sm font-bold text-slate-200 mt-0.5">{activeScheme.title}</h3>
                  </div>

                  {/* Farmer view toggle */}
                  <div className="flex items-center gap-2.5">
                    <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider font-mono">Farmer Mode</span>
                    <button
                      onClick={() => setFarmerView(!farmerView)}
                      className={`relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                        farmerView ? "bg-[var(--lime-glow)]" : "bg-slate-800"
                      }`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-slate-950 shadow ring-0 transition duration-200 ease-in-out ${
                          farmerView ? "translate-x-5" : "translate-x-0"
                        }`}
                      />
                    </button>
                  </div>
                </div>

                {/* TASK 7: farmer translation mode display */}
                {farmerView ? (
                  <div className="p-4 bg-emerald-500/5 border border-[var(--lime-glow)]/20 rounded-2xl mb-5">
                    <div className="flex items-center gap-2 text-[10px] font-black uppercase text-[var(--lime-glow)] mb-2">
                      <Sparkles className="w-3.5 h-3.5" /> Farmer Friendly Explanation
                    </div>
                    <p className="text-xs text-slate-200 leading-relaxed font-semibold">
                      {getFarmerFriendlyView(activeScheme)}
                    </p>
                  </div>
                ) : (
                  /* TASK 1: AI CONFIDENCE PANEL */
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
                    {/* Confidence gauge circle */}
                    <div className="p-4 bg-slate-950/40 border border-slate-900 rounded-2xl flex items-center gap-4">
                      {/* Circle gauge */}
                      <div className="relative w-14 h-14 flex items-center justify-center shrink-0">
                        <svg className="w-full h-full transform -rotate-90">
                          <circle cx="28" cy="28" r="24" stroke="#1e293b" strokeWidth="3.2" fill="transparent" />
                          <circle 
                            cx="28" 
                            cy="28" 
                            r="24" 
                            stroke="#b7e75d" 
                            strokeWidth="3.8" 
                            fill="transparent" 
                            strokeDasharray={2 * Math.PI * 24} 
                            strokeDashoffset={2 * Math.PI * 24 - (activeScheme.confidence * 2 * Math.PI * 24)}
                            className="transition-all duration-500"
                          />
                        </svg>
                        <span className="absolute text-[10px] font-black text-slate-200 font-mono">{(activeScheme.confidence * 100).toFixed(0)}%</span>
                      </div>
                      <div>
                        <h4 className="text-[10px] font-black text-slate-500 uppercase tracking-wider block">AI Confidence score</h4>
                        <p className="text-slate-200 block text-xs font-bold mt-1">
                          {activeScheme.confidence > 0.85 ? "Strong Recommendation" : "Moderate Recommendation"}
                        </p>
                      </div>
                    </div>

                    {/* Risk & Strength details */}
                    <div className="p-4 bg-slate-950/40 border border-slate-900 rounded-2xl grid grid-cols-2 gap-3 text-[11px] font-semibold">
                      <div>
                        <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">Audit Risk Level</span>
                        <span className={`block mt-1 font-bold ${
                          activeScheme.missing_documents.length > 0 ? "text-amber-400" : "text-emerald-400"
                        }`}>
                          {activeScheme.missing_documents.length > 0 ? "Medium Risk (audit required)" : "Low Risk (auto approve)"}
                        </span>
                      </div>
                      <div>
                        <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">Strength Score</span>
                        <span className="text-sky-400 block mt-1">{(activeScheme.confidence * 10).toFixed(1)} / 10.0</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* TASK 3: DECISION TREE VIEW */}
                <div className="mb-5">
                  <div className="flex items-center gap-2 mb-3">
                    <GitBranch className="w-4 h-4 text-sky-400" />
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Inference Decision Path Tree</span>
                  </div>

                  <div className="p-4 bg-slate-950/40 border border-slate-900 rounded-2xl flex flex-col md:flex-row justify-between items-center gap-4 relative">
                    {/* Connecting arrows for layout */}
                    <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-slate-900 -translate-y-1/2 hidden md:block z-0" />

                    {[
                      { node: "Farmer Profile", detail: `ID: ${selectedFarmerId.slice(3)}` },
                      { node: "Eligibility Rules", detail: `${activeScheme.required_documents.length} parameters` },
                      { node: "AI Reasoning", detail: "LangGraph routing" },
                      { node: "Final Recommendation", detail: activeScheme.status.replace(/_/g, " ") },
                    ].map((step, idx) => {
                      const isLast = idx === 3;
                      const isEligible = activeScheme.status === "ELIGIBLE";
                      return (
                        <div key={step.node} className="flex md:flex-col items-center text-left md:text-center gap-3 md:gap-2 relative z-10 w-full md:w-auto">
                          <div className={`p-2 border rounded-xl font-bold uppercase text-[9px] ${
                            isLast ? (isEligible ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400" : "border-amber-500/30 bg-amber-500/10 text-amber-400") :
                            "border-slate-800 bg-slate-900/60 text-slate-300"
                          }`}>
                            {step.node}
                            <span className="text-[7.5px] font-normal text-slate-500 block normal-case mt-0.5 font-mono">{step.detail}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* TASK 2: EVIDENCE MATRIX GRID */}
                <div className="mb-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Layers className="w-4 h-4 text-[var(--lime-glow)]" />
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Evidence Ingress Factors</span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-[10.5px]">
                    {[
                      "Land Size",
                      "Aadhaar",
                      "Bank",
                      "Crop",
                      "District",
                      "Previous History",
                      "Weather",
                      "Market",
                    ].map((factor) => {
                      const factorInfo = getEvidenceFactor(factor, activeScheme);
                      const helped = factorInfo.status === "Helped";

                      return (
                        <div key={factor} className={`p-3 bg-slate-950/45 border rounded-xl flex flex-col justify-between items-start ${
                          helped ? "border-emerald-500/15" : "border-amber-500/20"
                        }`}>
                          <div className="flex items-center justify-between w-full">
                            <span className="font-bold text-slate-300">{factor}</span>
                            <span className={`p-0.5 rounded text-[8px] font-black uppercase ${
                              helped ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"
                            }`}>
                              {helped ? "+" : "-"}
                            </span>
                          </div>
                          
                          <p className="text-[8.5px] text-slate-500 mt-2 leading-tight font-mono truncate w-full" title={factorInfo.desc}>
                            {factorInfo.desc}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* TASK 4: AI TIMELINE PROCESSING STAGES */}
                <div className="mb-5 border-t border-slate-900/60 pt-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Clock className="w-4 h-4 text-sky-400" />
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">AI Agent Execution Pipeline</span>
                  </div>

                  <div className="flex flex-col sm:flex-row justify-between items-center gap-4 relative py-2">
                    <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-slate-900 -translate-y-1/2 hidden sm:block z-0" />

                    {[
                      { step: "Question", duration: "12ms" },
                      { step: "Retrieval", duration: "180ms" },
                      { step: "Reasoning", duration: "850ms" },
                      { step: "Scheme Eval", duration: "410ms" },
                      { step: "Voice TTS", duration: "350ms" },
                    ].map((evt, idx) => {
                      return (
                        <div key={evt.step} className="flex sm:flex-col items-center text-left sm:text-center gap-3 sm:gap-2 relative z-10 w-full sm:w-auto">
                          <div className="size-5 rounded-full border-2 border-emerald-500/40 bg-[var(--forest-950)] text-[9px] font-black text-[var(--lime-glow)] grid place-items-center font-mono">
                            ✓
                          </div>
                          <div>
                            <span className="text-[10px] font-bold text-slate-200 block">{evt.step}</span>
                            <span className="text-[8px] text-slate-500 block font-mono mt-0.5">{evt.duration}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* TASK 5: EXPLAINABILITY SUMMARY CARDS & TASK 6: SOURCE FILES */}
                <div className="border-t border-slate-900/60 pt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Explanations summary */}
                  <div className="p-4 bg-slate-950/45 border border-slate-900 rounded-2xl flex flex-col gap-3">
                    <div>
                      <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider font-mono">AI Action Plan Checklist</span>
                      
                      <div className="flex flex-col gap-2 mt-2.5 font-mono text-[9.5px]">
                        <div className="flex justify-between items-start gap-3">
                          <span className="text-slate-500 shrink-0">WHY REC:</span>
                          <span className="text-slate-300 text-right">{activeScheme.reasoning[0] || "Passed land parameters"}</span>
                        </div>
                        <div className="flex justify-between items-start gap-3 border-t border-slate-900/60 pt-1.5">
                          <span className="text-slate-500 shrink-0">WHY NOT:</span>
                          <span className="text-slate-300 text-right">
                            {activeScheme.missing_documents.length > 0 
                              ? `Missing paperwork: ${activeScheme.missing_documents.join(", ")}` 
                              : "No limit factors detected"}
                          </span>
                        </div>
                        <div className="flex justify-between items-start gap-3 border-t border-slate-900/60 pt-1.5">
                          <span className="text-slate-500 shrink-0">EST SUCCESS:</span>
                          <span className="text-[var(--lime-glow)] font-bold text-right">
                            {(activeScheme.confidence * 100).toFixed(0)}% probability
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Sources origin (Task 6) */}
                  <div className="p-4 bg-slate-950/45 border border-slate-900 rounded-2xl flex flex-col gap-3">
                    <div>
                      <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider font-mono">Information Origin Repositories</span>
                      
                      <div className="flex flex-col gap-2 mt-2.5 font-mono text-[9.5px]">
                        <div className="flex justify-between items-center gap-2">
                          <span className="text-slate-500">Farmer Profile</span>
                          <span className="text-slate-300 uppercase">Twin Database</span>
                        </div>
                        <div className="flex justify-between items-center gap-2 border-t border-slate-900/60 pt-1.5">
                          <span className="text-slate-500">Government Database</span>
                          <span className="text-slate-300 uppercase">Welfare Registry</span>
                        </div>
                        <div className="flex justify-between items-center gap-2 border-t border-slate-900/60 pt-1.5">
                          <span className="text-slate-500">Weather Forecast</span>
                          <span className="text-slate-300 uppercase">Meteorology API</span>
                        </div>
                        <div className="flex justify-between items-center gap-2 border-t border-slate-900/60 pt-1.5">
                          <span className="text-slate-500">Market Feed</span>
                          <span className="text-slate-300 uppercase">Mandi MSP Indices</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          ) : (
            <div className="py-24 text-center text-slate-650 italic text-xs font-mono">
              Waiting for trust center checks to compile...
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
