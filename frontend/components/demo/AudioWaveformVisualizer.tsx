"use client";

import React, { useEffect, useRef, memo } from "react";

interface AudioWaveformVisualizerProps {
  isActive: boolean;
  isSpeaking?: boolean;
  isListening?: boolean;
}

/* ════════════════════════════════════════════════════════════
   AudioWaveformVisualizer — Canvas-based waveform animation.

   Crash-fix notes:
   - All animation is done via requestAnimationFrame on a Canvas.
   - We do NOT use framer-motion here to avoid animation-lifecycle
     conflicts during rapid state changes or fast scrolling.
   - Bar heights are computed deterministically from sine/cosine
     functions (no Math.random() on each frame) to keep React
     render output stable.
   - Cleanup cancels the RAF loop reliably to prevent memory leaks.
   ════════════════════════════════════════════════════════════ */

const BAR_COUNT = 24;

function AudioWaveformVisualizerInner({
  isActive,
  isSpeaking = false,
  isListening = false,
}: AudioWaveformVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const barsContainerRef = useRef<HTMLDivElement | null>(null);
  const rafRef = useRef<number>(0);
  const phaseRef = useRef(0);

  // ── Canvas sine-wave animation ──────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let running = true;

    const render = () => {
      if (!running) return;

      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);
      const centerY = height / 2;

      let baseAmp = 4;
      if (isSpeaking) baseAmp = 22;
      else if (isListening) baseAmp = 16;
      else if (isActive) baseAmp = 8;

      phaseRef.current += 0.06;
      const phase = phaseRef.current;

      const lines = [
        { color: "rgba(16,185,129,0.8)", freq: 0.03, ampScale: 1.0, speed: 1.0 },
        { color: "rgba(56,189,248,0.6)",  freq: 0.02, ampScale: 0.7, speed: 1.3 },
        { color: "rgba(168,85,247,0.4)",  freq: 0.04, ampScale: 0.5, speed: 0.8 },
      ];

      for (const line of lines) {
        ctx.beginPath();
        ctx.lineWidth = 2;
        ctx.strokeStyle = line.color;
        for (let x = 0; x < width; x++) {
          const amp =
            baseAmp *
            line.ampScale *
            (0.8 + 0.2 * Math.sin(phase * line.speed + x * 0.01));
          const y = centerY + Math.sin(x * line.freq + phase * line.speed) * amp;
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      }

      rafRef.current = requestAnimationFrame(render);
    };

    rafRef.current = requestAnimationFrame(render);

    return () => {
      running = false;
      cancelAnimationFrame(rafRef.current);
    };
  }, [isActive, isSpeaking, isListening]);

  // ── Deterministic bar heights via CSS animation + keyframes
  //    (no random values — stable across re-renders) ──────
  const barColor = isSpeaking
    ? "bg-emerald-400"
    : isListening
    ? "bg-cyan-400"
    : "bg-slate-700";

  return (
    <div className="relative my-4 flex flex-col items-center justify-center rounded-2xl border border-slate-800/80 bg-slate-900/60 p-3 backdrop-blur-md overflow-hidden">
      {/* Label */}
      <div className="absolute top-2 left-3 flex items-center gap-1.5 text-[10px] font-mono tracking-wider text-emerald-400">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />
        AUDIO STREAM VISUALIZER
      </div>

      {/* Sine-wave canvas */}
      <canvas
        ref={canvasRef}
        width={400}
        height={64}
        className="w-full h-16 rounded-lg bg-transparent"
      />

      {/* Frequency bars — deterministic heights via CSS transitions */}
      <div ref={barsContainerRef} className="mt-1 flex items-end justify-center gap-[3px]">
        {Array.from({ length: BAR_COUNT }).map((_, i) => {
          // Use a static sine offset per bar index to give varied but stable sizing
          const sinVal = Math.abs(Math.sin((i + 1) * 0.7));
          const baseH = isActive ? (isSpeaking ? 8 + sinVal * 22 : isListening ? 6 + sinVal * 14 : 4) : 3;
          return (
            <div
              key={i}
              className={`w-[3px] rounded-full ${barColor} transition-all`}
              style={{
                height: `${baseH}px`,
                animationName: isActive ? "waveBar" : "none",
                animationDuration: `${0.4 + (i % 6) * 0.08}s`,
                animationTimingFunction: "ease-in-out",
                animationIterationCount: "infinite",
                animationDirection: "alternate",
                animationDelay: `${(i % 8) * 0.05}s`,
              }}
            />
          );
        })}
      </div>

      {/* Keyframe styles injected inline via dangerouslySetInnerHTML to prevent React console warnings */}
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes waveBar {
          from { transform: scaleY(0.4); }
          to   { transform: scaleY(1.6); }
        }
      ` }} />
    </div>
  );
}

// Memoize to prevent unnecessary re-renders from parent scroll events
export const AudioWaveformVisualizer = memo(AudioWaveformVisualizerInner);
