import { motion } from "motion/react";
import { Sparkles } from "lucide-react";
import heroFields from "@/assets/hero-fields.jpg";

export function Hero() {
  return (
    <section className="relative overflow-hidden rounded-3xl">
      <div className="relative h-[280px] sm:h-[340px] lg:h-[400px]">
        <img
          src={heroFields}
          alt="Sunrise over lush terraced fields"
          width={1920}
          height={960}
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
              <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-white/80">
                Kisan Mitra AI · Waiting for backend
              </span>
            </div>
            <h1 className="font-display text-3xl font-bold tracking-tight text-white sm:text-4xl lg:text-5xl">
              Namaste, Admin <span className="gradient-text-sunrise">🌾</span>
            </h1>
            <p className="mt-2 max-w-lg text-sm text-white/70 sm:text-base">
              Live farmer, weather, mandi, and scheme data will appear here as
              soon as the platform connects to the backend.
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
