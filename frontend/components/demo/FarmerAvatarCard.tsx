"use client";

import React from "react";
import { motion } from "framer-motion";
import { MapPin, Sprout, Phone, ShieldCheck, User } from "lucide-react";
import { DemoFarmer } from "@/hooks/useDemoCallSession";

interface FarmerAvatarCardProps {
  farmer: DemoFarmer;
  callState: string;
}

export function FarmerAvatarCard({ farmer, callState }: FarmerAvatarCardProps) {
  const isConnected = callState === "connected" || callState === "listening" || callState === "processing" || callState === "speaking";

  return (
    <div className="flex flex-col items-center text-center my-3">
      {/* Avatar Container with Pulsing Ripple Aura */}
      <div className="relative mb-3">
        {isConnected && (
          <>
            <motion.div
              className="absolute -inset-4 rounded-full bg-emerald-500/20 blur-md"
              animate={{ scale: [1, 1.25, 1], opacity: [0.3, 0.7, 0.3] }}
              transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
            />
            <motion.div
              className="absolute -inset-8 rounded-full bg-cyan-500/10 blur-xl"
              animate={{ scale: [1.1, 1.4, 1.1], opacity: [0.2, 0.5, 0.2] }}
              transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
            />
          </>
        )}

        <div className="relative h-24 w-24 overflow-hidden rounded-full border-2 border-emerald-400/60 shadow-2xl bg-slate-900 flex items-center justify-center">
          <div className="h-full w-full bg-gradient-to-b from-emerald-800 to-slate-950 flex flex-col items-center justify-center text-emerald-200">
            <User className="w-12 h-12 stroke-1" />
          </div>
        </div>

        {/* Incoming call ring pulse badge */}
        {callState === "incoming" && (
          <span className="absolute -top-1 -right-1 flex h-4 w-4">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500 border border-slate-950"></span>
          </span>
        )}
      </div>

      <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-1.5">
        {farmer.name}
        <ShieldCheck className="w-4 h-4 text-emerald-400" />
      </h2>

      <div className="mt-1 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-300 font-sans">
        <span className="flex items-center gap-1 bg-slate-900/80 px-2.5 py-0.5 rounded-full border border-slate-800">
          <MapPin className="w-3 h-3 text-emerald-400" />
          {farmer.district}, {farmer.state}
        </span>
        <span className="flex items-center gap-1 bg-slate-900/80 px-2.5 py-0.5 rounded-full border border-slate-800">
          <Sprout className="w-3 h-3 text-emerald-400" />
          {farmer.land_hectares} Ha ({farmer.crops.join(", ")})
        </span>
        <span className="flex items-center gap-1 bg-slate-900/80 px-2.5 py-0.5 rounded-full border border-slate-800 font-mono text-[11px] text-emerald-300">
          <Phone className="w-3 h-3 text-emerald-400" />
          {farmer.phone}
        </span>
      </div>
    </div>
  );
}
