"use client";

import React, { useState, useEffect, useRef } from "react";
import { useDashboard } from "@/components/DashboardContext";
import {
  Play,
  Pause,
  ChevronRight,
  ChevronLeft,
  RotateCcw,
  Sparkles,
  Maximize2,
  Minimize2,
  Phone,
  MessageSquare,
  Server,
  BookOpen,
  Cpu,
  Layers,
  Volume2,
  Mail,
  Clock,
  User,
  AlertTriangle,
  Award,
  FileCheck2,
  Bookmark,
  Info
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
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Define 8 guided story steps (FEATURE 2)
const STORY_STEPS = [
  {
    step: 1,
    title: "Incoming Farmer Call",
    icon: <Phone className="w-4 h-4" />,
    wsEvent: "CALL_STARTED",
    explanation: "FastAPI gateway establishes IVR telephone trunk connection. Ingress routing captures caller ANI metadata."
  },
  {
    step: 2,
    title: "Language Detection",
    icon: <MessageSquare className="w-4 h-4" />,
    wsEvent: "CALLER_IDENTIFIED",
    explanation: "LangGraph language classification agent audits incoming voice stream to resolve dialect (Hindi, Kannada, Telugu)."
  },
  {
    step: 3,
    title: "Digital Twin Synthesis",
    icon: <Server className="w-4 h-4" />,
    wsEvent: "DIGITAL_TWIN_LOADED",
    explanation: "Retrieves agricultural records to rebuild the farmer's Digital Twin (hectares cultivated, historical crops, registry risk)."
  },
  {
    step: 4,
    title: "Knowledge Retrieval",
    icon: <BookOpen className="w-4 h-4" />,
    wsEvent: "SCHEME_SEARCH_STARTED",
    explanation: "Vector database (ChromaDB) queries central and state welfare scheme registry rules matching profile coordinates."
  },
  {
    step: 5,
    title: "AI Reasoning",
    icon: <Cpu className="w-4 h-4" />,
    wsEvent: "ELIGIBILITY_COMPLETED",
    explanation: "LangGraph multi-agent constraints checker audits profile parameters against registry criteria rules."
  },
  {
    step: 6,
    title: "Government Schemes",
    icon: <Layers className="w-4 h-4" />,
    wsEvent: "REASONING_COMPLETED",
    explanation: "Compiles final eligibility recommendations (e.g. PM-Kisan matching, PMFBY crop insurance approvals)."
  },
  {
    step: 7,
    title: "Voice Summary",
    icon: <Volume2 className="w-4 h-4" />,
    wsEvent: "VOICE_RESPONSE_STARTED",
    explanation: "Generates vernacular audio advice summary using text-to-speech engine playbacks for IVR trunk stream."
  },
  {
    step: 8,
    title: "SMS Summary Dispatch",
    icon: <Mail className="w-4 h-4" />,
    wsEvent: "CALL_COMPLETED",
    explanation: "SMS gateway dispatches clear application checklists and direct DBT links to the farmer's mobile device."
  }
];

interface PresentationDemoProps {
  onOpenDemo?: () => void;
}

export default function PresentationDemo({ onOpenDemo }: PresentationDemoProps = {}) {

  const { lastEvent, isConnected } = useDashboard();

  // Farmers list
  const [farmers, setFarmers] = useState<FarmerProfile[]>([]);
  const [selectedFarmerId, setSelectedFarmerId] = useState<string>("");
  const [activeStep, setActiveStep] = useState(0); // 0-indexed: 0 to 7
  const [isPlaying, setIsPlaying] = useState(false);
  const [autoMode, setAutoMode] = useState(true);
  const [fullscreen, setFullscreen] = useState(false);
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [reducedMotion, setReducedMotion] = useState(false);

  // References
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Initialize prefers-reduced-motion
  useEffect(() => {
    if (typeof window !== "undefined") {
      const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
      setReducedMotion(mediaQuery.matches);
    }
  }, []);

  // Fetch farmers list on load
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/demo/farmers`)
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        setFarmers(data);
        if (data.length > 0) {
          setSelectedFarmerId(data[0].farmer_id);
        }
      });
  }, []);

  // Timer tick effect (FEATURE 7)
  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        setTimerSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying]);

  // Handle auto-run steps transition
  useEffect(() => {
    if (isPlaying && autoMode) {
      const stepTimer = setInterval(() => {
        setActiveStep((prev) => {
          if (prev >= STORY_STEPS.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 3500); // advance every 3.5s in auto timeline simulation
      return () => clearInterval(stepTimer);
    }
  }, [isPlaying, autoMode]);

  // Reactive WebSocket event catcher: syncs active step with real-world simulator (FEATURE 4)
  useEffect(() => {
    if (lastEvent && autoMode) {
      const matchIdx = STORY_STEPS.findIndex(s => s.wsEvent === lastEvent.type);
      if (matchIdx !== -1) {
        setActiveStep(matchIdx);
        setIsPlaying(true);
      }
    }
  }, [lastEvent, autoMode]);

  const activeFarmer = farmers.find(f => f.farmer_id === selectedFarmerId);

  // Keyboards listeners (FEATURE 8)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space") {
        e.preventDefault();
        setIsPlaying((prev) => !prev);
      } else if (e.code === "ArrowRight") {
        e.preventDefault();
        handleNext();
      } else if (e.code === "ArrowLeft") {
        e.preventDefault();
        handlePrev();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Controls functions
  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleNext = () => {
    setActiveStep((prev) => Math.min(prev + 1, STORY_STEPS.length - 1));
  };

  const handlePrev = () => {
    setActiveStep((prev) => Math.max(prev - 1, 0));
  };

  const handleRestart = () => {
    setActiveStep(0);
    setTimerSeconds(0);
    setIsPlaying(false);
  };

  // Triggers live backend simulation
  const handleTriggerLiveSimulation = () => {
    if (!selectedFarmerId) return;
    handleRestart();
    setAutoMode(true);
    setIsPlaying(true);
    fetch(`${API_BASE}/api/v1/demo/simulate-call/${selectedFarmerId}`, { method: "POST" })
      .catch(() => {});
  };

  // Elapsed timer formatting
  const formatTimer = (totalSeconds: number) => {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  };

  // Executive summary parameters (FEATURE 6)
  const getExecutiveDetails = () => {
    if (!activeFarmer) return { name: "...", problem: "...", recommendation: "...", benefit: "...", docs: "...", confidence: "..." };
    const name = activeFarmer.name;
    const land = `${activeFarmer.land_hectares} Hectares`;
    
    // Custom mappings for demo farmers
    if (name.includes("Ramesh")) {
      return {
        name,
        problem: "Low crop yields & dry rainfall cycles",
        recommendation: "PM-Kisan land registry subsidy mapping",
        benefit: "Rs 6,000 / year direct cash transfer",
        docs: "Aadhaar Card, Land revenue record, bank account link",
        confidence: "98% (Verified Aadhaar)"
      };
    } else if (name.includes("Lakshmi")) {
      return {
        name,
        problem: "Access to credit & crop inputs procurement",
        recommendation: "Mahila Kisan Sashaktikaran Yojana integration",
        benefit: "Agricultural training, credit link, input subsidy",
        docs: "Aadhaar Card, Self Help Group membership ID",
        confidence: "95% (SHG Verified)"
      };
    } else if (name.includes("Priya")) {
      return {
        name,
        problem: "Organic transition expenses",
        recommendation: "Paramparagat Krishi Vikas Yojana (PKVY)",
        benefit: "Rs 50,000 / ha financial assistance for 3 years",
        docs: "Organic farming certificate, land maps",
        confidence: "94% (District committee verified)"
      };
    } else if (name.includes("Mohammed")) {
      return {
        name,
        problem: "Pest outbreak crop damage",
        recommendation: "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        benefit: "Insurance payouts for loss coverage",
        docs: "Insurance policy document, loss inspection report",
        confidence: "97% (Pest damage verified)"
      };
    } else {
      return {
        name,
        problem: "Retirement welfare savings link",
        recommendation: "PM Kisan Maan-Dhan Yojana (PM-KMY)",
        benefit: "Rs 3,000 / month pension after age 60",
        docs: "Aadhaar Card, Bank Passbook, age certificate",
        confidence: "96% (Aadhaar linked)"
      };
    }
  };

  const execData = getExecutiveDetails();
  const currentStepInfo = STORY_STEPS[activeStep];

  return (
    <div className={`flex flex-col gap-6 w-full ${
      fullscreen ? "fixed inset-0 bg-slate-950 z-50 p-6 md:p-10 overflow-y-auto" : ""
    }`}>
      
      {/* 🛠 DEMO CONTROLS TOOLBAR (FEATURE 3 & FEATURE 7) */}
      <div className="glass-panel border-2 border-slate-900 rounded-2xl p-4 flex flex-col md:flex-row justify-between items-center gap-4 z-10">
        <div className="flex items-center gap-4">
          <button
            onClick={handlePlayPause}
            className="p-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 rounded-full transition cursor-pointer"
            title={isPlaying ? "Pause Demo" : "Play Demo"}
          >
            {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current" />}
          </button>
          
          <button
            onClick={handlePrev}
            className="p-2 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded-xl transition cursor-pointer"
            title="Previous Step"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          
          <button
            onClick={handleNext}
            className="p-2 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded-xl transition cursor-pointer"
            title="Next Step"
          >
            <ChevronRight className="w-4 h-4" />
          </button>

          <button
            onClick={handleRestart}
            className="p-2 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded-xl transition cursor-pointer"
            title="Restart Demo"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <div className="h-6 w-px bg-slate-900" />

          {/* Auto Mode toggle */}
          <button
            onClick={() => setAutoMode(!autoMode)}
            className={`px-3 py-1.5 rounded-xl font-bold uppercase text-[9px] border transition ${
              autoMode ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-slate-950 text-slate-500 border-slate-900"
            }`}
          >
            {autoMode ? "Auto Play active" : "Manual steps"}
          </button>
          
          {/* Live Ingress simulator link */}
          <button
            onClick={handleTriggerLiveSimulation}
            className="px-3 py-1.5 bg-sky-500/10 text-sky-400 border border-sky-500/20 rounded-xl font-bold uppercase text-[9px] transition cursor-pointer hover:bg-sky-500/20"
          >
            Simulate Ingress Run
          </button>

          {/* Launch Live Phone Call Demo */}
          {onOpenDemo && (
            <button
              onClick={onOpenDemo}
              className="px-3.5 py-1.5 bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white rounded-xl font-bold uppercase text-[10px] transition cursor-pointer shadow-md shadow-emerald-950/50 flex items-center gap-1.5 animate-pulse"
            >
              <Phone className="w-3.5 h-3.5" />
              <span>Launch Live Phone Call</span>
            </button>
          )}
        </div>


        {/* Timer & Fullscreen */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-slate-950 border border-slate-900 rounded-xl px-3 py-1.5 font-mono">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-300 font-bold">{formatTimer(timerSeconds)}</span>
          </div>

          <button
            onClick={() => setFullscreen(!fullscreen)}
            className="p-2.5 bg-slate-900 hover:bg-slate-800 text-slate-200 hover:text-white rounded-xl transition cursor-pointer"
            title={fullscreen ? "Exit Fullscreen" : "Go Fullscreen"}
          >
            {fullscreen ? <Minimize2 className="w-4 h-4 text-sky-400" /> : <Maximize2 className="w-4 h-4 text-[var(--lime-glow)]" />}
          </button>
        </div>
      </div>

      {/* ── CENTRAL STORYBOARD WORKSPACE (FEATURE 1, 2, 4, 5, 6) ────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start z-10">
        
        {/* LEFT COLUMN: GUIDED STORY TIMELINE (FEATURE 2 & 4) */}
        <div className="lg:col-span-7 flex flex-col gap-4 max-h-[580px] overflow-y-auto pr-1 mc-scrollbar">
          <div className="flex justify-between items-center px-1">
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-wider font-mono">
              Guided System Storyboard
            </span>
            <span className="text-[9px] font-mono text-sky-400">
              Step {activeStep + 1} of 8
            </span>
          </div>

          {STORY_STEPS.map((step, idx) => {
            const isActive = idx === activeStep;
            const isCompleted = idx < activeStep;

            return (
              <div
                key={step.step}
                onClick={() => {
                  setActiveStep(idx);
                  setAutoMode(false); // Switch to manual walk on click
                }}
                className={`glass-panel border-2 rounded-2xl p-4 cursor-pointer text-left transition-all duration-200 flex items-start gap-4 relative ${
                  isActive ? "border-[var(--lime-glow)]/30 bg-emerald-500/5 shadow-md" :
                  isCompleted ? "border-slate-900/60 bg-slate-900/10 text-slate-400 opacity-75" :
                  "border-slate-900 text-slate-600"
                }`}
              >
                {/* Visual completion bullet */}
                <div className={`size-7 rounded-full border-2 grid place-items-center text-[10px] font-black shrink-0 ${
                  isCompleted ? "border-emerald-500 bg-[var(--forest-950)] text-[var(--lime-glow)]" :
                  isActive ? "border-[var(--lime-glow)] bg-emerald-500/10 text-[var(--lime-glow)] animate-pulse" :
                  "border-slate-800 bg-slate-950 text-slate-650"
                }`}>
                  {isCompleted ? "✓" : step.step}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="shrink-0 text-slate-500">{step.icon}</span>
                    <h3 className={`text-xs font-bold leading-tight ${isActive ? "text-slate-200" : "text-slate-450"}`}>
                      {step.title}
                    </h3>
                  </div>
                  
                  {isActive && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-[10px] text-slate-400 leading-relaxed mt-2 font-mono bg-slate-950 border border-slate-900/60 rounded-xl p-2.5"
                    >
                      {step.explanation}
                    </motion.p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* RIGHT COLUMN: EXECUTIVE SUMMARY & STORY PANEL DETAILS (FEATURE 5 & 6) */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          {/* FEATURE 5: AI STORY PANEL */}
          <div className="glass-panel border border-slate-900 rounded-3xl p-5">
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-mono block mb-3">
              AI Process Explanation
            </span>
            <div className="p-4 bg-slate-950/45 border border-slate-900 rounded-2xl">
              <div className="flex items-center gap-2 text-[10px] font-black uppercase text-[var(--lime-glow)] font-mono mb-2">
                <Sparkles className="w-3.5 h-3.5 text-[var(--lime-glow)]" /> Explainable Agent Loop
              </div>
              <p className={`text-slate-200 leading-relaxed font-semibold transition-all duration-300 ${
                fullscreen ? "text-sm" : "text-xs"
              }`}>
                {currentStepInfo.explanation}
              </p>
            </div>
          </div>

          {/* FEATURE 6: EXECUTIVE SUMMARY SCORECARD */}
          <div className="glass-panel border border-slate-900 rounded-3xl p-5">
            <div className="flex items-center gap-2 border-b border-slate-900 pb-3 mb-4">
              <Bookmark className="w-4 h-4 text-sky-400" />
              <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest font-mono">
                Executive Case Summary
              </span>
            </div>

            <div className="flex flex-col gap-3.5 font-mono text-[10.5px]">
              <div className="flex justify-between items-start gap-4">
                <span className="text-slate-500 shrink-0 uppercase tracking-wider">Farmer:</span>
                <span className="text-slate-200 text-right font-bold">{execData.name}</span>
              </div>
              <div className="flex justify-between items-start gap-4 border-t border-slate-900/60 pt-2">
                <span className="text-slate-500 shrink-0 uppercase tracking-wider">Core Issue:</span>
                <span className="text-slate-350 text-right">{execData.problem}</span>
              </div>
              <div className="flex justify-between items-start gap-4 border-t border-slate-900/60 pt-2">
                <span className="text-slate-500 shrink-0 uppercase tracking-wider">Recommendation:</span>
                <span className="text-emerald-400 text-right font-bold">{execData.recommendation}</span>
              </div>
              <div className="flex justify-between items-start gap-4 border-t border-slate-900/60 pt-2">
                <span className="text-slate-500 shrink-0 uppercase tracking-wider">Benefits:</span>
                <span className="text-[var(--lime-glow)] text-right font-bold">{execData.benefit}</span>
              </div>
              <div className="flex justify-between items-start gap-4 border-t border-slate-900/60 pt-2">
                <span className="text-slate-500 shrink-0 uppercase tracking-wider">Papers Required:</span>
                <span className="text-slate-350 text-right leading-tight max-w-[240px]">{execData.docs}</span>
              </div>
              <div className="flex justify-between items-center gap-4 border-t border-slate-900/60 pt-2">
                <span className="text-slate-500 shrink-0 uppercase tracking-wider">Decision confidence:</span>
                <span className="text-sky-400 font-bold">{execData.confidence}</span>
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
