import { motion } from "motion/react";
import indiaMap from "@/assets/india-map.jpg";
import { MapPin } from "lucide-react";

export function IndiaMap() {
  return (
    <div className="glass-panel relative overflow-hidden rounded-3xl">
      <div className="flex items-center justify-between p-5">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--lime-glow)]">
            Geospatial
          </div>
          <h2 className="mt-1 font-display text-xl font-bold sm:text-2xl">India Operations Map</h2>
        </div>
        <div className="hidden gap-1.5 rounded-full bg-black/20 p-1 sm:flex">
          {["Weather", "Markets", "Diseases"].map((t, i) => (
            <button
              key={t}
              className={[
                "rounded-full px-3 py-1 text-[11px] font-semibold transition",
                i === 0 ? "bg-[var(--lime-glow)] text-[var(--forest-950)]" : "text-white/60 hover:text-white",
              ].join(" ")}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="relative aspect-[6/5] w-full sm:aspect-[16/10]">
        <img
          src={indiaMap}
          alt="India agricultural operations map"
          width={1200}
          height={1000}
          loading="lazy"
          className="absolute inset-0 h-full w-full object-cover opacity-90 mix-blend-screen"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[var(--forest-950)]/70" />

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4 }}
          className="absolute inset-0 grid place-items-center"
        >
          <div className="rounded-2xl border border-dashed border-white/15 bg-black/30 px-5 py-4 text-center backdrop-blur-md">
            <div className="text-mono text-[10px] uppercase tracking-widest text-white/50">
              No live map markers
            </div>
            <div className="mt-1 text-sm font-semibold text-white/80">
              Waiting for backend geospatial feed
            </div>
          </div>
        </motion.div>

        <div className="glass-panel absolute right-4 top-4 rounded-xl px-3 py-2">
          <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-white/60">
            <MapPin className="size-3" /> — states
          </div>
          <div className="mt-0.5 font-display text-lg font-bold text-white/70">— villages</div>
        </div>
      </div>
    </div>
  );
}
