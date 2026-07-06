"use client";

import React from "react";
import { useDashboard } from "@/components/DashboardContext";
import { 
  Radio, 
  Server, 
  MessageSquare, 
  Cpu, 
  List, 
  HardDrive, 
  Phone, 
  Mail, 
  ShieldCheck, 
  RefreshCw, 
  BookOpen, 
  Terminal, 
  Settings,
  Menu,
  Landmark,
  Sparkles
} from "lucide-react";

export default function LeftSidebar() {
  const { activeTab, setActiveTab } = useDashboard();

  const navigationGroups = [
    {
      title: "Core Operations",
      items: [
        { id: "mission-control", label: "Mission Control", icon: <Radio className="w-4 h-4" /> },
        { id: "overview", label: "Digital Twin", icon: <Server className="w-4 h-4" /> },
        { id: "schemes", label: "Welfare Schemes", icon: <Landmark className="w-4 h-4" /> },
        { id: "platform", label: "Reasoning", icon: <MessageSquare className="w-4 h-4" /> },
        { id: "demo", label: "Solve for Tomorrow", icon: <Sparkles className="w-4 h-4" /> },
        { id: "knowledge", label: "Knowledge", icon: <BookOpen className="w-4 h-4" /> }
      ]
    },
    {
      title: "Channels",
      items: [
        { id: "telephony", label: "Telephony & IVR", icon: <Phone className="w-4 h-4" /> },
        { id: "sms", label: "SMS Gateway", icon: <Mail className="w-4 h-4" /> },
        { id: "media", label: "Media Ingestion", icon: <HardDrive className="w-4 h-4" /> }
      ]
    },
    {
      title: "Management",
      items: [
        { id: "ai", label: "AI Specialist Hub", icon: <Cpu className="w-4 h-4" /> },
        { id: "conversations", label: "Conversations Monitor", icon: <List className="w-4 h-4" /> },
        { id: "governance", label: "Governance & Registry", icon: <ShieldCheck className="w-4 h-4" /> },
        { id: "integrations", label: "Integrations", icon: <RefreshCw className="w-4 h-4" /> },
        { id: "telemetry", label: "Analytics", icon: <Terminal className="w-4 h-4" /> },
        { id: "settings", label: "Settings", icon: <Settings className="w-4 h-4" /> }
      ]
    }
  ];

  return (
    <aside className="w-64 bg-slate-950/20 border-r border-slate-900/60 p-4 flex flex-col gap-6 select-none shrink-0 h-[calc(100vh-53px)] overflow-y-auto mc-scrollbar">
      {navigationGroups.map((group) => (
        <div key={group.title} className="flex flex-col gap-1.5">
          <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest px-3 mb-1 block">
            {group.title}
          </span>
          <nav className="flex flex-col gap-1">
            {group.items.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-left text-xs font-semibold tracking-wide transition-all border cursor-pointer ${
                    isActive
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/40 border-transparent"
                  }`}
                >
                  <span className={`transition-transform duration-200 ${isActive ? "scale-110" : ""}`}>
                    {item.icon}
                  </span>
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>
      ))}
    </aside>
  );
}
