"use client";

import { useState, useCallback, useRef, useEffect, useMemo } from "react";
import { getApiBase } from "@/lib/utils";

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

export interface VoiceEngineStatus {
  languageCode: string;
  languageLabel: string;
  engineType: "native" | "cloud_neural";
  engineName: string;
  statusText: string;
  isCloudFallback: boolean;
}

export function useTextToSpeech(currentLanguage: string = "kn-IN") {
  const [isPlaying, setIsPlaying] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const fallbackTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      const updateVoices = () => {
        const available = window.speechSynthesis.getVoices();
        if (available.length > 0) setVoices(available);
      };
      updateVoices();
      window.speechSynthesis.onvoiceschanged = updateVoices;
      return () => {
        if ("speechSynthesis" in window) {
          window.speechSynthesis.onvoiceschanged = null;
        }
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

      const target = (langTag || "kn-IN").toLowerCase().replace("_", "-");
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

  /**
   * Reactive voiceEngineStatus — updates INSTANTLY whenever currentLanguage changes
   */
  const voiceStatus: VoiceEngineStatus = useMemo(() => {
    const target = (currentLanguage || "kn-IN").toLowerCase().replace("_", "-");
    const shortCode = target.split("-")[0];
    const cfg = LANG_CONFIG[target] || { label: currentLanguage || "Language", keywords: [shortCode] };
    const label = cfg.label;

    const available =
      typeof window !== "undefined" && "speechSynthesis" in window
        ? window.speechSynthesis.getVoices().length > 0
          ? window.speechSynthesis.getVoices()
          : voices
        : voices;

    const nativeVoice = selectBestNativeVoice(currentLanguage, available);

    if (nativeVoice) {
      return {
        languageCode: currentLanguage,
        languageLabel: label,
        engineType: "native",
        engineName: nativeVoice.name,
        statusText: `Native Browser Voice • ${label}`,
        isCloudFallback: false,
      };
    }

    return {
      languageCode: currentLanguage,
      languageLabel: label,
      engineType: "cloud_neural",
      engineName: "Cloud Neural Voice",
      statusText: `Cloud Neural Voice • ${label}`,
      isCloudFallback: true,
    };
  }, [currentLanguage, voices, selectBestNativeVoice]);

  // Backward compatibility warning string derived dynamically from active language
  const ttsWarning = voiceStatus.isCloudFallback
    ? `${voiceStatus.languageLabel} voice is unavailable on this device. Using cloud neural voice.`
    : null;

  const speak = useCallback(
    (text: string, language = "hi-IN", onEnd?: () => void, audioUrl?: string) => {
      if (typeof window === "undefined") {
        onEnd?.();
        return;
      }

      if (fallbackTimerRef.current) clearTimeout(fallbackTimerRef.current);

      const target = language.toLowerCase().replace("_", "-");
      const shortCode = target.split("-")[0];
      const langConfig = LANG_CONFIG[target] || { label: language, keywords: [shortCode] };

      const availableVoices =
        typeof window !== "undefined" && "speechSynthesis" in window
          ? window.speechSynthesis.getVoices().length > 0
            ? window.speechSynthesis.getVoices()
            : voices
          : [];

      const handleSpeechEnd = () => {
        if (fallbackTimerRef.current) clearTimeout(fallbackTimerRef.current);
        setIsPlaying(false);
        onEnd?.();
      };

      // Direct custom audio URL provided
      if (audioUrl) {
        if (audioRef.current) audioRef.current.pause();
        const audio = new Audio(audioUrl);
        audioRef.current = audio;
        audio.onplay = () => setIsPlaying(true);
        audio.onended = handleSpeechEnd;
        audio.onerror = handleSpeechEnd;
        audio.play().catch(handleSpeechEnd);
        return;
      }

      // Check for native browser voice
      const nativeVoice = selectBestNativeVoice(language, availableVoices);

      if (nativeVoice && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = language;
        utterance.voice = nativeVoice;
        utterance.rate = 0.9;
        utterance.pitch = 1.0;

        utterance.onstart = () => setIsPlaying(true);
        utterance.onend = handleSpeechEnd;
        utterance.onerror = (e) => {
          if ((e as any).error !== "interrupted") {
            console.warn("[TTS] Native SpeechSynthesis error:", (e as any).error);
          }
          handleSpeechEnd();
        };

        window.speechSynthesis.speak(utterance);
      } else {
        // Fallback: Cloud Neural TTS Endpoint & direct MP3 fallback
        const API_BASE = getApiBase();
        const cloudTtsUrl = `${API_BASE}/api/v1/demo/tts?text=${encodeURIComponent(text.slice(0, 350))}&lang=${shortCode}`;
        const directGoogleUrl = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encodeURIComponent(text.slice(0, 350))}&tl=${shortCode}&client=tw-ob`;

        if (audioRef.current) audioRef.current.pause();

        const tryPlayAudio = (url: string, isRetry = false) => {
          const audio = new Audio(url);
          audioRef.current = audio;

          audio.onplay = () => {
            if (fallbackTimerRef.current) clearTimeout(fallbackTimerRef.current);
            setIsPlaying(true);
          };

          audio.onended = handleSpeechEnd;

          audio.onerror = () => {
            if (!isRetry) {
              tryPlayAudio(directGoogleUrl, true);
            } else {
              // Speech simulation timer if browser audio autoplay policy blocks audio playback
              setIsPlaying(true);
              const duration = Math.min(6000, Math.max(2500, text.length * 40));
              fallbackTimerRef.current = setTimeout(handleSpeechEnd, duration);
            }
          };

          audio.play().catch(() => {
            if (!isRetry) {
              tryPlayAudio(directGoogleUrl, true);
            } else {
              setIsPlaying(true);
              const duration = Math.min(6000, Math.max(2500, text.length * 40));
              fallbackTimerRef.current = setTimeout(handleSpeechEnd, duration);
            }
          });
        };

        tryPlayAudio(cloudTtsUrl);
      }
    },
    [selectBestNativeVoice, voices]
  );

  const stop = useCallback(() => {
    if (typeof window !== "undefined") {
      if (fallbackTimerRef.current) clearTimeout(fallbackTimerRef.current);
      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
      if (audioRef.current) audioRef.current.pause();
      setIsPlaying(false);
    }
  }, []);

  return { isPlaying, speak, stop, voices, voiceStatus, ttsWarning };
}
