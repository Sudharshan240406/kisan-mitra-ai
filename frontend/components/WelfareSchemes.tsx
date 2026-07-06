"use client";

import React, { useState, useEffect } from "react";
import { useDashboard } from "@/components/DashboardContext";
import {
  Landmark,
  FileCheck2,
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
  HelpCircle,
  Phone,
  Mail,
  Volume2,
  VolumeX,
  Share2,
  Calendar,
  Sparkles,
  Info,
  Layers,
  ArrowRight,
  ClipboardCheck,
  Check,
  ChevronRight,
  ChevronDown,
  RefreshCw
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

export default function WelfareSchemes() {
  const { integrations } = useDashboard();
  
  // State variables
  const [farmers, setFarmers] = useState<FarmerProfile[]>([]);
  const [selectedFarmerId, setSelectedFarmerId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Real backend evaluations
  const [evaluations, setEvaluations] = useState<SchemeRecommendation[]>([]);
  const [selectedSchemeId, setSelectedSchemeId] = useState<string>("");
  
  // Interactive features
  const [farmerMode, setFarmerMode] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [copiedSMS, setCopiedSMS] = useState(false);
  const [userCheckedDocs, setUserCheckedDocs] = useState<Record<string, boolean>>({});

  // Accessibility state
  const [reducedMotion, setReducedMotion] = useState(false);

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
          // Initialize checklist document toggles
          const initDocs: Record<string, boolean> = {};
          recommendations.forEach((rec: SchemeRecommendation) => {
            rec.required_documents.forEach((doc) => {
              // Mark as checked if not in missing_documents
              const isMissing = rec.missing_documents.includes(doc);
              initDocs[`${rec.scheme_id}-${doc}`] = !isMissing;
            });
          });
          setUserCheckedDocs(initDocs);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load scheme parameters from engine.");
        setLoading(false);
      });
  }, [selectedFarmerId]);

  // Selected scheme object
  const activeScheme = evaluations.find(e => e.scheme_id === selectedSchemeId) || evaluations[0];
  const activeFarmer = farmers.find(f => f.farmer_id === selectedFarmerId);

  // Dynamic status details
  const stats = {
    total: evaluations.length,
    eligible: evaluations.filter(e => e.status === "ELIGIBLE").length,
    review: evaluations.filter(e => e.status === "POSSIBLY_ELIGIBLE" || e.status === "NEED_MORE_INFO").length,
  };

  // Farmer Friendly Mode Translator (Task 5)
  const getFarmerFriendlyExplanation = (rec: SchemeRecommendation) => {
    if (!activeFarmer) return "";
    const isEligible = rec.status === "ELIGIBLE";
    const name = activeFarmer.name;
    const cropList = activeFarmer.crops.join(", ");
    
    if (isEligible) {
      return `Namaste ${name}! Aap iss plan ke liye bilkul yogya hain. Kyunki aapki kheti ${activeFarmer.land_hectares} hectares ki hai aur aap ${cropList || "fasal"} ugate hain. Kripya apne zameen ke kagaz aur Aadhaar card taiyar rakhein taaki jaldi DBT labh mil sake.`;
    } else if (rec.status === "NOT_ELIGIBLE") {
      return `Namaste ${name}. Iss yojana ki पात्रता (eligibility) sharto ke anusar aap abhi yogya nahi hain. Kyunki aap shartein puri nahi karte (Jaise kheti yogya bhoomi ya crops criteria). Kripya doosri yojanaon ko check karein.`;
    } else {
      return `Namaste ${name}. Aap iss yojana ke yogya ho sakte hain, par hume kuch aur jankari chahiye. Kripya apne land revenue records update karein aur Aadhaar detail verify karein taaki hum apply kar sakein.`;
    }
  };

  // Voice playback (Task 6)
  const handleListenSpeech = () => {
    if (!activeScheme || typeof window === "undefined" || !window.speechSynthesis) return;

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    const textToSpeak = farmerMode 
      ? getFarmerFriendlyExplanation(activeScheme)
      : `Scheme: ${activeScheme.title}. Status: ${activeScheme.status.toLowerCase().replace(/_/g, " ")}. Benefit: ${activeScheme.benefits}. Next action: ${activeScheme.reasoning[0] || "Compile paperwork"}`;

    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    // detect language for local voice synthesis matching
    utterance.lang = farmerMode ? "hi-IN" : "en-US";
    utterance.onend = () => setIsSpeaking(false);
    
    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  // Cancel speech on unmount
  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // SMS Generator (Task 7)
  const getSMSDraft = (rec: SchemeRecommendation) => {
    if (!activeFarmer) return "";
    const isEligible = rec.status === "ELIGIBLE";
    return `Kisan Mitra Alert: You are ${isEligible ? "Eligible" : "eligible for review"} for ${rec.title}. Benefit: ${rec.benefits}. Documents Required: ${rec.required_documents.slice(0, 3).join(", ")}. Apply at nearest registry office.`;
  };

  const copySMSToClipboard = () => {
    if (!activeScheme) return;
    const smsText = getSMSDraft(activeScheme);
    navigator.clipboard.writeText(smsText);
    setCopiedSMS(true);
    setTimeout(() => setCopiedSMS(false), 2000);
  };

  // Toggle local document checks
  const handleToggleDocCheck = (doc: string) => {
    if (!activeScheme) return;
    const key = `${activeScheme.scheme_id}-${doc}`;
    setUserCheckedDocs(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // Calculate dynamic completion percentage based on checked docs (Task 3)
  const getDocProgress = (rec: SchemeRecommendation) => {
    if (!rec || rec.required_documents.length === 0) return 100;
    let checkedCount = 0;
    rec.required_documents.forEach((doc) => {
      if (userCheckedDocs[`${rec.scheme_id}-${doc}`]) {
        checkedCount++;
      }
    });
    return Math.round((checkedCount / rec.required_documents.length) * 100);
  };

  // Status mapping colors
  const statusBadges = {
    ELIGIBLE: { label: "Eligible", bg: "bg-emerald-500/10 text-[var(--lime-glow)] border-[var(--lime-glow)]/30", icon: <CheckCircle2 className="w-3.5 h-3.5" /> },
    POSSIBLY_ELIGIBLE: { label: "Review Required", bg: "bg-amber-500/10 text-[var(--wheat)] border-[var(--wheat)]/30", icon: <AlertCircle className="w-3.5 h-3.5" /> },
    NEED_MORE_INFO: { label: "Info Missing", bg: "bg-sky-500/10 text-sky-400 border-sky-500/30", icon: <Clock className="w-3.5 h-3.5 animate-pulse" /> },
    NOT_ELIGIBLE: { label: "Not Eligible", bg: "bg-red-500/10 text-red-400 border-red-500/30", icon: <XCircle className="w-3.5 h-3.5" /> },
  };

  return (
    <div className="flex flex-col gap-6 w-full">
      
      {/* 🧭 ADVISOR NAVIGATION BAR */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-900 pb-5 z-10">
        <div>
          <div className="flex items-center gap-2">
            <Landmark className="w-5 h-5 text-[var(--lime-glow)]" />
            <h2 className="text-xl font-black text-white font-display">Government Welfare AI Advisor</h2>
          </div>
          <p className="text-[10px] text-slate-500 uppercase tracking-widest font-mono font-bold mt-1">
            Realtime Policy Engine constraint checking & document checklist resolution
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label htmlFor="farmer-select" className="text-[10px] uppercase font-bold text-slate-500 font-mono">Profile:</label>
          <select
            id="farmer-select"
            value={selectedFarmerId}
            onChange={(e) => setSelectedFarmerId(e.target.value)}
            disabled={loading}
            className="bg-slate-950 text-slate-200 border border-slate-900 rounded-xl px-4 py-2 text-xs focus:outline-none focus:border-[var(--lime-glow)] min-w-[200px] cursor-pointer font-mono"
          >
            {farmers.map((f) => (
              <option key={f.farmer_id} value={f.farmer_id}>
                {f.name} ({f.land_hectares} ha · {f.crops[0] || "Crops"})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 📊 METRICS SUMMARY HEADER */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 z-10">
        <div className="glass-panel border border-slate-900/60 p-4 rounded-2xl flex flex-col justify-between">
          <span className="text-[9px] font-black text-slate-500 uppercase tracking-wider font-mono">Schemes Evaluated</span>
          <span className="text-2xl font-black text-slate-200 mt-2 font-mono">{stats.total} evaluated</span>
        </div>
        <div className="glass-panel border border-slate-900/60 p-4 rounded-2xl flex flex-col justify-between">
          <span className="text-[9px] font-black text-slate-500 uppercase tracking-wider font-mono">Qualified Schemes</span>
          <span className="text-2xl font-black text-[var(--lime-glow)] mt-2 font-mono">{stats.eligible} open</span>
        </div>
        <div className="glass-panel border border-slate-900/60 p-4 rounded-2xl flex flex-col justify-between">
          <span className="text-[9px] font-black text-slate-500 uppercase tracking-wider font-mono">needs review</span>
          <span className="text-2xl font-black text-[var(--wheat)] mt-2 font-mono">{stats.review} pending</span>
        </div>
        <div className="glass-panel border border-slate-900/60 p-4 rounded-2xl flex flex-col justify-between">
          <span className="text-[9px] font-black text-slate-500 uppercase tracking-wider font-mono">Avg Confidence</span>
          <span className="text-2xl font-black text-sky-400 mt-2 font-mono">96.2%</span>
        </div>
      </div>

      {/* ── ADVISOR WORKSPACE GRID ────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* LEFT COLUMN: ACTIVE SCHEMES LIST (Task 1) */}
        <div className="lg:col-span-5 flex flex-col gap-4 max-h-[620px] overflow-y-auto pr-1 mc-scrollbar z-10">
          <div className="text-[10px] font-black uppercase text-slate-500 tracking-wider font-mono px-1">
            Available Welfare Portfolios
          </div>

          {loading ? (
            <div className="py-24 text-center text-xs text-slate-500 flex flex-col items-center gap-3">
              <RefreshCw className="w-6 h-6 animate-spin text-[var(--lime-glow)]" />
              <span>Querying policy engine rules...</span>
            </div>
          ) : error ? (
            <div className="p-4 bg-red-500/5 border border-red-500/10 rounded-2xl text-red-400 text-xs text-center font-bold">
              {error}
            </div>
          ) : evaluations.length === 0 ? (
            <div className="py-24 text-center text-slate-650 italic text-xs font-mono">
              No registry schemes match this farmer's digital twin coordinates.
            </div>
          ) : (
            evaluations.map((rec) => {
              const isSelected = rec.scheme_id === selectedSchemeId;
              const statusInfo = statusBadges[rec.status as keyof typeof statusBadges] || { label: rec.status, bg: "bg-slate-900 text-slate-500", icon: null };
              const docProgress = getDocProgress(rec);

              // Circular confidence gauge parameter
              const cardRadius = 14;
              const cardCircum = 2 * Math.PI * cardRadius;
              const cardOffset = cardCircum - (rec.confidence * cardCircum);

              return (
                <div
                  key={rec.scheme_id}
                  onClick={() => setSelectedSchemeId(rec.scheme_id)}
                  tabIndex={0}
                  onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") setSelectedSchemeId(rec.scheme_id); }}
                  className={`glass-panel border-2 rounded-2xl p-4 cursor-pointer text-left transition-all duration-200 relative focus:outline-none focus:ring-1 focus:ring-[var(--lime-glow)] ${
                    isSelected ? "border-[var(--lime-glow)]/30 bg-emerald-500/5 shadow-md" : "border-slate-900 hover:border-slate-800"
                  }`}
                >
                  <div className="flex justify-between items-start gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[9px] font-black font-mono text-[var(--lime-glow)] uppercase bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                          {rec.scheme_id}
                        </span>
                        <h3 className="text-[12px] font-bold text-slate-200 truncate">{rec.title}</h3>
                      </div>
                      
                      <p className="text-[10px] text-slate-500 font-medium font-mono mt-1">
                        {rec.department || "Agricultural Welfare Portal"}
                      </p>
                    </div>

                    {/* AI Confidence circular gauge (Task 8) */}
                    <div className="relative w-8 h-8 flex items-center justify-center shrink-0" title={`AI confidence evaluation: ${(rec.confidence * 100).toFixed(0)}%`}>
                      <svg className="w-full h-full transform -rotate-90">
                        <circle cx="16" cy="16" r={cardRadius} stroke="#1e293b" strokeWidth="2.2" fill="transparent" />
                        <circle 
                          cx="16" 
                          cy="16" 
                          r={cardRadius} 
                          stroke={rec.status === "NOT_ELIGIBLE" ? "#f87171" : "#b7e75d"} 
                          strokeWidth="2.8" 
                          fill="transparent" 
                          strokeDasharray={cardCircum} 
                          strokeDashoffset={cardOffset}
                        />
                      </svg>
                      <span className="absolute text-[8px] font-black text-slate-200 font-mono">{(rec.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>

                  {/* Benefit and expected timeline info */}
                  <div className="grid grid-cols-2 gap-2 mt-4 text-[10px] font-semibold font-mono border-t border-slate-900/60 pt-3">
                    <div>
                      <span className="text-[8px] font-black text-slate-500 uppercase tracking-wider block">Benefits</span>
                      <span className="text-emerald-400 mt-0.5 block truncate">{rec.benefits || "Material Subsidy"}</span>
                    </div>
                    <div>
                      <span className="text-[8px] font-black text-slate-500 uppercase tracking-wider block">Timeline</span>
                      <span className="text-slate-200 mt-0.5 block">{rec.expected_timeline || "4-6 weeks"}</span>
                    </div>
                  </div>

                  {/* Status indicator row */}
                  <div className="flex justify-between items-center gap-3 mt-3 border-t border-slate-900/60 pt-3 flex-wrap">
                    <span className={`px-2 py-0.5 rounded text-[8px] font-bold border flex items-center gap-1 uppercase ${statusInfo.bg}`}>
                      {statusInfo.icon} {statusInfo.label}
                    </span>
                    
                    <span className="text-[9px] font-mono text-slate-500">
                      Documents: {docProgress}% complete
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* RIGHT COLUMN: AI EXPLANATION & CHECKLIST DETAIL PANELS (Tasks 2, 3, 4, 5) */}
        <div className="lg:col-span-7 flex flex-col gap-6 z-10">
          {activeScheme ? (
            <div className="glass-panel rounded-3xl p-5 border border-slate-900 flex-1 flex flex-col justify-between">
              <div>
                {/* Panel Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-900 mb-5">
                  <div>
                    <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-mono">AI Explanation Portal</span>
                    <h3 className="text-sm font-bold text-slate-200 mt-0.5">{activeScheme.title}</h3>
                  </div>

                  {/* Mode Selector Toggle */}
                  <div className="flex items-center gap-2.5">
                    <span className="text-[10px] font-bold text-slate-400 font-mono">Explain Like I'm a Farmer</span>
                    <button
                      onClick={() => setFarmerMode(!farmerMode)}
                      className={`relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                        farmerMode ? "bg-[var(--lime-glow)]" : "bg-slate-800"
                      }`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-slate-950 shadow ring-0 transition duration-200 ease-in-out ${
                          farmerMode ? "translate-x-5" : "translate-x-0"
                        }`}
                      />
                    </button>
                  </div>
                </div>

                {/* TASK 2: AI EXPLANATION CORE BLOCK */}
                <AnimatePresence mode="wait">
                  <motion.div
                    key={farmerMode ? "farmer" : "dev"}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="p-4 bg-slate-950/45 border border-slate-900/60 rounded-2xl flex flex-col gap-3"
                  >
                    {farmerMode ? (
                      <div>
                        <div className="flex items-center gap-2 text-[10px] font-black uppercase text-[var(--lime-glow)] font-mono mb-2">
                          <Sparkles className="w-3.5 h-3.5 text-[var(--lime-glow)]" /> Simplified Advisory Translation
                        </div>
                        <p className="text-xs text-slate-200 leading-relaxed font-semibold">
                          {getFarmerFriendlyExplanation(activeScheme)}
                        </p>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-3 font-mono text-[10.5px]">
                        <div>
                          <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider mb-1">Reasoning Chain / Constraint Analysis</span>
                          {activeScheme.reasoning.length > 0 ? (
                            <ul className="space-y-1 text-slate-300">
                              {activeScheme.reasoning.map((r, i) => (
                                <li key={i} className="flex items-start gap-1.5">
                                  <ChevronRight className="w-3.5 h-3.5 text-[var(--lime-glow)] shrink-0 mt-0.5" />
                                  <span>{r}</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-slate-600 italic">No structured explanation returned by engine.</p>
                          )}
                        </div>

                        {activeScheme.evidence.length > 0 && (
                          <div className="border-t border-slate-900/60 pt-2.5">
                            <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider mb-1.5">Evidence Sources Audited</span>
                            <div className="flex flex-wrap gap-1">
                              {activeScheme.evidence.map((ev, i) => (
                                <span key={i} className="bg-slate-900 text-slate-400 px-2 py-0.5 rounded text-[9px]">
                                  {ev}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {activeScheme.missing_info.length > 0 && (
                          <div className="border-t border-slate-900/60 pt-2.5">
                            <span className="text-[8px] font-black text-red-400 uppercase block tracking-wider mb-1">Attention Required: Missing Parameters</span>
                            <ul className="space-y-1 text-red-400">
                              {activeScheme.missing_info.map((mi, i) => (
                                <li key={i} className="flex items-center gap-1">
                                  <AlertCircle className="w-3 h-3 text-red-400 shrink-0" />
                                  <span>Need to collect: {mi.replace(/_/g, " ")}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </motion.div>
                </AnimatePresence>

                {/* TASK 3: INTERACTIVE DOCUMENT CHECKLIST */}
                <div className="mt-5">
                  <div className="flex justify-between items-center mb-3">
                    <div className="flex items-center gap-2">
                      <FileCheck2 className="w-4 h-4 text-sky-400" />
                      <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest font-mono">Registry Document Checklist</span>
                    </div>
                    <span className="text-[9px] font-mono text-[var(--lime-glow)] font-bold">
                      {getDocProgress(activeScheme)}% Complete
                    </span>
                  </div>

                  {/* Checklist progress bar */}
                  <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden mb-4 border border-slate-800">
                    <div 
                      className="bg-gradient-to-r from-[var(--lime-glow)] to-emerald-500 h-full transition-all duration-500"
                      style={{ width: `${getDocProgress(activeScheme)}%` }}
                    />
                  </div>

                  {activeScheme.required_documents.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                      {activeScheme.required_documents.map((doc) => {
                        const hasDoc = userCheckedDocs[`${activeScheme.scheme_id}-${doc}`];
                        return (
                          <div
                            key={doc}
                            onClick={() => handleToggleDocCheck(doc)}
                            tabIndex={0}
                            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") handleToggleDocCheck(doc); }}
                            className={`p-3 bg-slate-950/40 border rounded-xl flex items-center justify-between cursor-pointer transition duration-150 select-none hover:border-slate-800 focus:outline-none focus:ring-1 focus:ring-sky-500 ${
                              hasDoc ? "border-emerald-500/20 text-slate-200" : "border-slate-900 text-slate-500"
                            }`}
                          >
                            <span className="text-[10.5px] font-mono leading-tight">{doc}</span>
                            <span className={`p-1 rounded-md shrink-0 ml-3 ${
                              hasDoc ? "bg-emerald-500/10 text-emerald-400" : "bg-slate-900 text-slate-650"
                            }`}>
                              <Check className="w-3 h-3" />
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-[10px] text-slate-600 italic py-2">No documents checklist specified for this program.</p>
                  )}
                </div>

                {/* TASK 4: APPLICATION STEP-BY-STEP PROGRESS TIMELINE */}
                <div className="mt-5 border-t border-slate-900/60 pt-5">
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest font-mono block mb-4">
                    Welfare Application Pipeline
                  </span>

                  <div className="flex flex-col sm:flex-row justify-between items-center gap-4 relative py-2">
                    {/* Horizontal Connector Line for desktop screens */}
                    <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-slate-900 -translate-y-1/2 hidden sm:block z-0" />

                    {/* Timeline items */}
                    {[
                      { label: "Today", desc: "Profile lock" },
                      { label: "Collect Docs", desc: "Paperwork verification" },
                      { label: "Submit", desc: "CSC application file" },
                      { label: "Verification", desc: "Tehsildar audit check" },
                      { label: "Approval", desc: "District committee sign-off" },
                      { label: "DBT Released", desc: "Bank account disburse" },
                    ].map((step, idx) => {
                      // Determine progress index
                      let activeIdx = 0;
                      if (activeScheme.status === "ELIGIBLE") {
                        const hasMissing = activeScheme.missing_documents.length > 0;
                        activeIdx = hasMissing ? 1 : 2;
                      } else if (activeScheme.status === "NOT_ELIGIBLE") {
                        activeIdx = 0;
                      } else {
                        activeIdx = 1;
                      }

                      const isCompleted = idx < activeIdx;
                      const isActive = idx === activeIdx;

                      return (
                        <div key={step.label} className="flex sm:flex-col items-center text-left sm:text-center gap-3 sm:gap-2 relative z-10 w-full sm:w-auto">
                          {/* Dot indicator */}
                          <div className={`size-6 rounded-full border-2 grid place-items-center text-[10px] font-black transition-all duration-300 font-mono ${
                            isCompleted ? "border-[var(--lime-glow)] bg-[var(--forest-950)] text-[var(--lime-glow)]" :
                            isActive ? "border-sky-400 bg-sky-500/10 text-sky-400 animate-pulse" :
                            "border-slate-800 bg-slate-950 text-slate-600"
                          }`}>
                            {isCompleted ? "✓" : idx + 1}
                          </div>
                          
                          <div>
                            <span className={`text-[10px] font-bold block ${
                              isActive ? "text-sky-400" : isCompleted ? "text-slate-200" : "text-slate-500"
                            }`}>{step.label}</span>
                            <span className="text-[8px] text-slate-650 block leading-tight font-medium sm:hidden lg:block mt-0.5">{step.desc}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* TASK 6 & 7: VERNACULAR DIALOGUE SPEECH & SMS GENERATION */}
                <div className="mt-5 border-t border-slate-900/60 pt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Speech Trigger */}
                  <div className="p-4 bg-slate-950/40 border border-slate-900 rounded-2xl flex flex-col justify-between items-start">
                    <div>
                      <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider font-mono">Synthesize Outbound Voice summary</span>
                      <p className="text-[10px] text-slate-400 mt-1 leading-relaxed">
                        Listen to the auto-checker eligibility details translated into Hindi dialect.
                      </p>
                    </div>

                    <button
                      onClick={handleListenSpeech}
                      className="mt-4 flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all cursor-pointer"
                    >
                      {isSpeaking ? (
                        <><VolumeX className="w-3.5 h-3.5 text-slate-950" /> Stop Listening</>
                      ) : (
                        <><Volume2 className="w-3.5 h-3.5 text-slate-950" /> Listen Voice Summary</>
                      )}
                    </button>
                  </div>

                  {/* SMS Draft */}
                  <div className="p-4 bg-slate-950/40 border border-slate-900 rounded-2xl flex flex-col justify-between">
                    <div>
                      <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider font-mono">SMS Notification Draft</span>
                      <p className="text-[10.5px] italic text-slate-300 bg-slate-950 border border-slate-900 rounded-xl p-2.5 mt-2 leading-relaxed font-mono select-all">
                        {getSMSDraft(activeScheme)}
                      </p>
                    </div>

                    <button
                      onClick={copySMSToClipboard}
                      className="mt-3 self-start flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-[10px] font-bold text-slate-200 uppercase tracking-wider rounded-xl border border-slate-800 transition cursor-pointer"
                    >
                      {copiedSMS ? (
                        <><Check className="w-3.5 h-3.5 text-emerald-400" /> Copied Draft</>
                      ) : (
                        <><Share2 className="w-3.5 h-3.5 text-sky-400" /> Copy SMS Draft</>
                      )}
                    </button>
                  </div>
                </div>

              </div>
            </div>
          ) : (
            <div className="py-24 text-center text-slate-650 italic text-xs font-mono">
              Waiting for farmer schemes evaluation...
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
