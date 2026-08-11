"use client";

import React from "react";
import { MessageSquare, User, Bot } from "lucide-react";

export interface TranscriptLine {
  role: string;
  text: string;
  timestamp: number;
}

export interface TranscriptViewerProps {
  transcript: TranscriptLine[];
  callActive?: boolean;
}

export function TranscriptViewer({ transcript, callActive }: TranscriptViewerProps) {
  return (
    <div className="glass-panel border border-slate-900 rounded-3xl p-5 space-y-3">
      <div className="flex items-center justify-between border-b border-slate-900 pb-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-emerald-400" />
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
            Live Multilingual Transcript
          </h4>
        </div>
        {callActive && (
          <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[9px] font-mono font-bold border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" /> Streaming
          </span>
        )}
      </div>

      <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1 mc-scrollbar">
        {transcript.length === 0 ? (
          <div className="text-[10px] text-slate-600 italic py-8 text-center font-mono">
            No active session lines recorded yet. Start simulation or place a query.
          </div>
        ) : (
          transcript.map((line, idx) => {
            const isUser = line.role === "user" || line.role === "farmer";
            return (
              <div
                key={idx}
                className={`flex gap-2.5 p-3 rounded-2xl border text-[11px] leading-relaxed transition ${
                  isUser
                    ? "bg-slate-950/80 border-slate-800/80 text-slate-200"
                    : "bg-emerald-950/20 border-emerald-500/20 text-emerald-100"
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                    isUser ? "bg-slate-800 text-slate-400" : "bg-emerald-500/20 text-emerald-400"
                  }`}
                >
                  {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex justify-between items-center text-[9px] text-slate-500 font-mono">
                    <span className="font-bold uppercase">{line.role}</span>
                    <span>{new Date(line.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-slate-300 font-sans">{line.text}</p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
