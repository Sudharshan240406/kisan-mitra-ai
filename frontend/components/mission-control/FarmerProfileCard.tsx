"use client";

import React from "react";
import { User, MapPin, Sprout, ShieldCheck, Award } from "lucide-react";

export interface FarmerProfileProps {
  farmer: {
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
    caste?: string;
    recent_damage?: string | null;
    is_organic?: boolean;
    is_tenant?: boolean;
    digital_twin_version?: string;
    profile_completeness?: number;
    last_interaction?: string;
    risk_profile?: string;
  } | null;
  selectedFarmerId?: string;
  onSelectFarmer?: (farmerId: string) => void;
  availableFarmers?: Array<{ farmer_id: string; name: string; state: string }>;
}

export function FarmerProfileCard({
  farmer,
  selectedFarmerId,
  onSelectFarmer,
  availableFarmers = []
}: FarmerProfileProps) {
  if (!farmer) {
    return (
      <div className="glass-panel border border-slate-900 rounded-3xl p-5 text-center">
        <User className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        <h4 className="text-sm font-bold text-slate-400">Digital Twin Unloaded</h4>
        <p className="text-[10px] text-slate-600 mt-1">Select a farmer profile or initiate a call to load state data.</p>
        
        {availableFarmers.length > 0 && onSelectFarmer && (
          <div className="mt-4 flex flex-wrap gap-2 justify-center">
            {availableFarmers.map((f) => (
              <button
                key={f.farmer_id}
                onClick={() => onSelectFarmer(f.farmer_id)}
                className={`px-2.5 py-1 text-[10px] rounded-lg border font-mono transition ${
                  selectedFarmerId === f.farmer_id
                    ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                    : "bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700"
                }`}
              >
                {f.name} ({f.state})
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="glass-panel border border-slate-900 rounded-3xl p-5 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-900 pb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-sm">
            {farmer.name.charAt(0)}
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-200">{farmer.name}</h3>
            <span className="text-[10px] text-slate-500 font-mono">ID: {farmer.farmer_id} • {farmer.language}</span>
          </div>
        </div>
        <span className="px-2 py-0.5 rounded-full text-[9px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          DBT Verified
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-[10.5px] font-mono">
        <div className="p-2.5 bg-slate-950/60 border border-slate-900 rounded-xl">
          <span className="text-[9px] text-slate-500 uppercase tracking-wider block">Location</span>
          <span className="text-slate-300 font-semibold">{farmer.district}, {farmer.state}</span>
        </div>
        <div className="p-2.5 bg-slate-950/60 border border-slate-900 rounded-xl">
          <span className="text-[9px] text-slate-500 uppercase tracking-wider block">Land Size</span>
          <span className="text-slate-300 font-semibold">{farmer.land_hectares} Hectares</span>
        </div>
      </div>

      <div>
        <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider block mb-1.5">Active Crops</span>
        <div className="flex flex-wrap gap-1.5">
          {farmer.crops.map((crop, i) => (
            <span key={i} className="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 text-slate-300 text-[10px] font-mono">
              🌾 {crop}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
