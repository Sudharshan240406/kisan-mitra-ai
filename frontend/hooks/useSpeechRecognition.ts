"use client";

import { useState, useEffect, useCallback, useRef } from "react";

export interface SpeechRecognitionHookOptions {
  language?: string;
  onResult?: (transcript: string, isFinal: boolean) => void;
  onError?: (error: string) => void;
}

/* ════════════════════════════════════════════════════════════
   useSpeechRecognition — Stable Web Speech API wrapper.

   Key behaviours:
   - language prop drives recognition.lang; when it changes and
     the mic is currently listening, recognition restarts
     automatically so STT always uses the selected language.
   - No auto language detection logic — the caller controls lang.
   - Refs track the recognition instance to avoid stale closures.
   ════════════════════════════════════════════════════════════ */

export function useSpeechRecognition(options: SpeechRecognitionHookOptions = {}) {
  const { language = "en-IN", onResult, onError } = options;

  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [isSupported, setIsSupported] = useState(false);

  const recognitionRef = useRef<any>(null);
  const isListeningRef = useRef(false);
  const languageRef = useRef(language);
  const onResultRef = useRef(onResult);
  const onErrorRef = useRef(onError);

  // Keep refs current without re-creating callbacks
  useEffect(() => { languageRef.current = language; }, [language]);
  useEffect(() => { onResultRef.current = onResult; }, [onResult]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      setIsSupported(!!SR);
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.onend = null; // prevent auto-restart on manual stop
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    isListeningRef.current = false;
    setIsListening(false);
  }, []);

  const startListening = useCallback(() => {
    if (typeof window === "undefined") return;

    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      onErrorRef.current?.("Browser speech recognition is not supported.");
      return;
    }

    try {
      // Stop existing session first
      if (recognitionRef.current) {
        recognitionRef.current.onend = null;
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }

      const recognition = new SR();
      recognition.lang = languageRef.current; // always use selected language
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onstart = () => {
        isListeningRef.current = true;
        setIsListening(true);
        setTranscript("");
        setInterimTranscript("");
      };

      recognition.onresult = (event: any) => {
        let finalStr = "";
        let interimStr = "";

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const res = event.results[i];
          if (res.isFinal) {
            finalStr += res[0].transcript;
          } else {
            interimStr += res[0].transcript;
          }
        }

        if (finalStr) {
          setTranscript((prev) => (prev ? `${prev} ${finalStr}` : finalStr));
          onResultRef.current?.(finalStr, true);
        }
        if (interimStr) {
          setInterimTranscript(interimStr);
          onResultRef.current?.(interimStr, false);
        }
      };

      recognition.onerror = (event: any) => {
        // "no-speech" and "aborted" are benign
        if (event.error !== "no-speech" && event.error !== "aborted") {
          console.warn("[SpeechRecognition] Error:", event.error);
          onErrorRef.current?.(event.error);
        }
        isListeningRef.current = false;
        setIsListening(false);
      };

      recognition.onend = () => {
        isListeningRef.current = false;
        setIsListening(false);
      };

      recognition.start();
      recognitionRef.current = recognition;
    } catch (err: any) {
      console.error("[SpeechRecognition] Failed to start:", err);
      isListeningRef.current = false;
      setIsListening(false);
      onErrorRef.current?.(err.message || "Failed to start speech recognition.");
    }
  }, []); // stable — uses refs internally

  const resetTranscript = useCallback(() => {
    setTranscript("");
    setInterimTranscript("");
  }, []);

  // When language changes while listening, restart with new language
  useEffect(() => {
    if (isListeningRef.current) {
      // Restart with new language automatically
      startListening();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.onend = null;
        recognitionRef.current.stop();
      }
    };
  }, []);

  return {
    isListening,
    transcript,
    interimTranscript,
    isSupported,
    startListening,
    stopListening,
    resetTranscript,
    setTranscript,
  };
}
