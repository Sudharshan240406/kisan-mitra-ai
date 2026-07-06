"use client";

import React from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

export function Hero() {
  const heroFields = "/assets/hero-fields.jpg";
  
  return (
    <section className="relative overflow-hidden rounded-3xl z-10">
      <div className="relative h-[240px] sm:h-[280px] lg:h-[320px]">
        <img
          src={heroFields}
          alt="Sunrise over lush terraced fields"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[var(--forest-950)] via-[var(--forest-950)]/50 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-r from-[var(--forest-950)]/80 via-transparent to-transparent" />

        <div className="relative flex h-full flex-col justify-end p-6 sm:p-8 lg:p-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            className="max-w-2xl"
          >
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 backdrop-blur-md">
              <Sparkles className="size-3 text-[var(--lime-glow)]" />
              <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/80">
                Kisan Mitra AI · Operations Console
              </span>
            </div>
            <h1 className="font-display text-2xl font-black tracking-tight text-white sm:text-3xl lg:text-4xl">
              Namaste, Administrator <span className="gradient-text-sunrise">🌾</span>
            </h1>
            <p className="mt-2 max-w-lg text-xs text-white/70 sm:text-sm">
              Live farmer calls, telemetry, and scheme updates are connected in real-time.
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
