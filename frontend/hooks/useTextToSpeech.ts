"use client";

import { useState, useCallback, useRef, useEffect } from "react";

/* ════════════════════════════════════════════════════════════════
   LANGUAGE → VOICE KEYWORD MAPPING & LABELS
   Maps each supported language code to search terms used to find
   the best available browser voice for that language.
   NEVER falls back to an English voice for Indian languages.
   ════════════════════════════════════════════════════════════════ */

const LANG_CONFIG: Record<string, { label: string; keywords: string[] }> = {
  "en-in": { label: "English",   keywords: ["en-in", "english india", "india", "en_in", "en-us", "en-gb"] },
  "hi-in": { label: "Hindi",     keywords: ["hi-in", "hindi", "hi_in", "हिन्दी", "hi"] },
  "kn-in": { label: "Kannada",   keywords: ["kn-in", "kannada", "kn_in", "ಕನ್ನಡ", "kn"] },
  "te-in": { label: "Telugu",    keywords: ["te-in", "telugu", "te_in", "తెలుగు", "te"] },
  "ta-in": { label: "Tamil",     keywords: ["ta-in", "tamil", "ta_in", "தமிழ்", "ta"] },
  "ml-in": { label: "Malayalam", keywords: ["ml-in", "malayalam", "ml_in", "മലയാളം", "ml"] },
  "mr-in": { label: "Marathi",   keywords: ["mr-in", "marathi", "mr_in", "मराठी", "mr"] },
  "pa-in": { label: "Punjabi",   keywords: ["pa-in", "punjabi", "pa_in", "ਪੰਜਾਬੀ", "pa"] },
  "gu-in": { label: "Gujarati",  keywords: ["gu-in", "gujarati", "gu_in", "ગુજરાતી", "gu"] },
  "bn-in": { label: "Bengali",   keywords: ["bn-in", "bengali", "bangla", "bn_in", "বাংলা", "bn"] },
};

export function useTextToSpeech() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [ttsWarning, setTtsWarning] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      const updateVoices = () => {
        const available = window.speechSynthesis.getVoices();
        if (available.length > 0) setVoices(available);
      };
      updateVoices();
      window.speechSynthesis.onvoiceschanged = updateVoices;
      return () => {
        window.speechSynthesis.onvoiceschanged = null;
      };
    }
  }, []);

  /**
   * selectBestNativeVoice — Returns a matching native SpeechSynthesisVoice
   * for non-English languages ONLY if the voice actually speaks that language.
   * NEVER returns an English voice for Kannada, Telugu, Hindi, etc.
   */
  const selectBestNativeVoice = useCallback(
    (langTag: string, allVoices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null => {
      if (!allVoices || allVoices.length === 0) return null;

      const target = langTag.toLowerCase().replace("_", "-");
      const shortCode = target.split("-")[0];
      const cfg = LANG_CONFIG[target] || { label: langTag, keywords: [shortCode] };

      // 1. Exact BCP-47 match (e.g. "kn-IN")
      let match = allVoices.find(
        (v) => v.lang.toLowerCase().replace("_", "-") === target
      );
      if (match) return match;

      // 2. Starts with short language code (e.g. "kn") BUT strictly NOT English when target is not English
      match = allVoices.find((v) => {
        const vLang = v.lang.toLowerCase();
        if (shortCode !== "en" && (vLang.startsWith("en") || v.name.toLowerCase().includes("english"))) {
          return false;
        }
        return vLang.startsWith(shortCode);
      });
      if (match) return match;

      // 3. Match by language keyword in voice name/lang
      for (const kw of cfg.keywords) {
        if (kw === "en" || kw === "en-us" || kw === "en-gb") continue; // skip English keywords for non-English target
        match = allVoices.find((v) => {
          const vName = v.name.toLowerCase();
          const vLang = v.lang.toLowerCase();
          if (shortCode !== "en" && (vLang.startsWith("en") || vName.includes("english"))) {
            return false;
          }
          return vName.includes(kw) || vLang.includes(kw);
        });
        if (match) return match;
      }

      // If non-English and no native voice found, return null (STRICT)
      return null;
    },
    []
  );

  const speak = useCallback(
    (text: string, language = "hi-IN", onEnd?: () => void, audioUrl?: string) => {
      if (typeof window === "undefined") {
        onEnd?.();
        return;
      }

      const target = language.toLowerCase().replace("_", "-");
      const shortCode = target.split("-")[0];
      const langConfig = LANG_CONFIG[target] || { label: language, keywords: [shortCode] };

      const availableVoices =
        typeof window !== "undefined" && "speechSynthesis" in window
          ? window.speechSynthesis.getVoices().length > 0
            ? window.speechSynthesis.getVoices()
            : voices
          : [];

      // Log requested speech diagnostics
      console.log("[TTS] Requested language:", language, `(${langConfig.label})`);
      console.log(
        "[TTS] Available SpeechSynthesis voices:",
        availableVoices.map((v) => `${v.name} (${v.lang})`)
      );

      // Direct custom audio URL provided
      if (audioUrl) {
        console.log("[TTS] Provider: Custom Audio URL");
        if (audioRef.current) audioRef.current.pause();
        const audio = new Audio(audioUrl);
        audioRef.current = audio;
        audio.onplay = () => setIsPlaying(true);
        audio.onended = () => {
          setIsPlaying(false);
          onEnd?.();
        };
        audio.onerror = () => {
          setIsPlaying(false);
          onEnd?.();
        };
        audio.play().catch(() => {
          setIsPlaying(false);
          onEnd?.();
        });
        return;
      }

      // Check for native browser voice
      const nativeVoice = selectBestNativeVoice(language, availableVoices);

      if (nativeVoice) {
        // Option A: Browser has a native voice for this language
        console.log("[TTS] Selected voice:", nativeVoice.name);
        console.log("[TTS] Provider: Browser SpeechSynthesis");
        console.log("[TTS] SpeechSynthesis Voice:", nativeVoice);
        setTtsWarning(null);

        if ("speechSynthesis" in window) {
          window.speechSynthesis.cancel();

          const utterance = new SpeechSynthesisUtterance(text);
          utterance.lang = language;
          utterance.voice = nativeVoice;
          utterance.rate = 0.9;
          utterance.pitch = 1.0;

          utterance.onstart = () => setIsPlaying(true);
          utterance.onend = () => {
            setIsPlaying(false);
            onEnd?.();
          };
          utterance.onerror = (e) => {
            if ((e as any).error !== "interrupted") {
              console.warn("[TTS] Error:", (e as any).error);
            }
            setIsPlaying(false);
            onEnd?.();
          };

          window.speechSynthesis.speak(utterance);
        } else {
          onEnd?.();
        }
      } else {
        // Option B: Browser lacks native voice for this language
        // DO NOT use English! Trigger Cloud Neural Voice & show warning banner.
        const warningMsg = `${langConfig.label} voice is unavailable on this device. Using cloud neural voice.`;
        const fallbackReason = `Browser lacks native voice for ${langConfig.label} (${language}). Available voices count: ${availableVoices.length}.`;
        
        console.warn(`[TTS] Fallback reason: ${fallbackReason}`);
        console.log(`[TTS] Requested language: ${language} (${langConfig.label})`);
        console.log(`[TTS] Selected voice: Cloud Neural Voice (${shortCode}-IN)`);
        console.log(`[TTS] Voice provider: Google/Edge Cloud Neural Speech`);
        console.log(`[TTS] SpeechSynthesis voice: null (Native browser voice unavailable for ${shortCode})`);
        console.log(`[TTS] Available voices:`, availableVoices.map((v) => `${v.name} (${v.lang})`));
        
        setTtsWarning(warningMsg);

        // Synthesize via Backend Cloud Neural TTS Audio Stream Endpoint
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const cloudTtsUrl = `${API_BASE}/api/v1/demo/tts?text=${encodeURIComponent(text.slice(0, 400))}&lang=${shortCode}`;

        if (audioRef.current) audioRef.current.pause();
        const audio = new Audio(cloudTtsUrl);
        audioRef.current = audio;

        audio.onplay = () => setIsPlaying(true);
        audio.onended = () => {
          setIsPlaying(false);
          onEnd?.();
        };
        audio.onerror = (e) => {
          console.warn("[TTS] Backend Cloud Neural Voice stream fallback error:", e);
          setIsPlaying(false);
          onEnd?.();
        };

        audio.play().catch((err) => {
          console.warn("[TTS] Audio play exception:", err);
          setIsPlaying(false);
          onEnd?.();
        });
      }
    },
    [selectBestNativeVoice, voices]
  );

  const stop = useCallback(() => {
    if (typeof window !== "undefined") {
      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
      if (audioRef.current) audioRef.current.pause();
      setIsPlaying(false);
    }
  }, []);

  return { isPlaying, speak, stop, voices, ttsWarning };
}
