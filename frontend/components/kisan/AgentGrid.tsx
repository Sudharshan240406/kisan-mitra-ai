"use client";

import React from "react";
import { useDashboard } from "@/components/DashboardContext";
import { Bot, Cpu } from "lucide-react";
import { motion } from "framer-motion";

export function AgentGrid() {
  const { agents } = useDashboard();

  return (
    <div className="glass-panel rounded-3xl p-5 sm:p-6 z-10">
      <div className="mb-5 flex items-end justify-between">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--lime-glow)]">
            Neural Fleet
          </div>
          <h2 className="mt-1 font-display text-base font-bold sm:text-lg">AI Agent Command</h2>
        </div>
      </div>
      
      <div className="flex flex-col gap-2.5 max-h-[320px] overflow-y-auto pr-1 mc-scrollbar">
        {agents.map((agent, index) => {
          const isRunning = agent.status === "running";
          return (
            <motion.div
              key={agent.name}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex items-center justify-between p-3.5 bg-slate-950/40 border border-slate-900/60 rounded-xl hover:border-slate-800 transition duration-200"
            >
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${isRunning ? "bg-emerald-500/10 text-emerald-400 animate-pulse" : "bg-slate-900 text-slate-400"}`}>
                  {agent.icon || <Cpu className="w-4 h-4" />}
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-200">{agent.name}</h4>
                  <p className="text-[10px] text-slate-500 font-medium mt-0.5">{agent.role}</p>
                </div>
              </div>

              <div className="text-right">
                <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                  isRunning ? "bg-emerald-500/10 text-emerald-400 animate-pulse" : "bg-slate-900 text-slate-400"
                }`}>
                  {agent.status}
                </span>
                <p className="text-[9px] text-slate-500 font-mono mt-1">Lat: {agent.latency}</p>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
