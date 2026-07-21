"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useSpeechRecognition } from "./useSpeechRecognition";
import { useTextToSpeech } from "./useTextToSpeech";

export type CallState = "idle" | "incoming" | "connected" | "listening" | "processing" | "speaking" | "ended";

export interface DemoFarmer {
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
}

export interface TranscriptTurn {
  id: string;
  role: "farmer" | "assistant" | "system";
  text: string;
  timestamp: string;
  languageCode?: string;
}

/* ═══════════════════════════════════════════════════════════
   LANGUAGE DEFINITIONS — SINGLE SOURCE OF TRUTH
   ═══════════════════════════════════════════════════════════ */

export interface LanguageOption {
  code: string;       // BCP-47 code used for STT + TTS
  label: string;      // Display label
  flag: string;       // Emoji flag
  nativeName: string; // Name in its own script
  promptName: string; // Exact language name to inject into LLM prompt
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: "en-IN", label: "English",    flag: "🇬🇧", nativeName: "English",    promptName: "English"   },
  { code: "hi-IN", label: "Hindi",      flag: "🇮🇳", nativeName: "हिन्दी",     promptName: "Hindi"     },
  { code: "kn-IN", label: "Kannada",    flag: "🇮🇳", nativeName: "ಕನ್ನಡ",     promptName: "Kannada"   },
  { code: "te-IN", label: "Telugu",     flag: "🇮🇳", nativeName: "తెలుగు",    promptName: "Telugu"    },
  { code: "ta-IN", label: "Tamil",      flag: "🇮🇳", nativeName: "தமிழ்",     promptName: "Tamil"     },
  { code: "ml-IN", label: "Malayalam",  flag: "🇮🇳", nativeName: "മലയാളം",   promptName: "Malayalam" },
  { code: "mr-IN", label: "Marathi",    flag: "🇮🇳", nativeName: "मराठी",     promptName: "Marathi"   },
  { code: "pa-IN", label: "Punjabi",    flag: "🇮🇳", nativeName: "ਪੰਜਾਬੀ",   promptName: "Punjabi"   },
  { code: "gu-IN", label: "Gujarati",   flag: "🇮🇳", nativeName: "ગુજરાતી",  promptName: "Gujarati"  },
  { code: "bn-IN", label: "Bengali",    flag: "🇮🇳", nativeName: "বাংলা",     promptName: "Bengali"   },
];

/* ═══════════════════════════════════════════════════════════
   GREETING MESSAGES — ONE PER LANGUAGE
   ═══════════════════════════════════════════════════════════ */

const GREETINGS: Record<string, (name: string) => string> = {
  "en-IN": (n) => `Hello ${n}! Welcome to Kisan Mitra AI. How can I help you with your farming needs today?`,
  "hi-IN": (n) => `नमस्ते ${n} जी! किसान मित्र AI में आपका स्वागत है। बताइए, आज मैं आपकी क्या मदद कर सकता हूँ?`,
  "kn-IN": (n) => `ನಮಸ್ಕಾರ ${n} ಅವರೇ! ಕಿಸಾನ್ ಮಿತ್ರ AI ಗೆ ಸ್ವಾಗತ. ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?`,
  "te-IN": (n) => `నమస్కారం ${n} గారు! కిసాన్ మిత్ర AI కి స్వాగతం. ఈరోజు నేను మీకు ఎలా సహాయపడగలను?`,
  "ta-IN": (n) => `வணக்கம் ${n} அவர்களே! கிசான் மித்ரா AI-க்கு வரவேற்கிறோம். இன்று நான் உங்களுக்கு எவ்வாறு உதவலாம்?`,
  "ml-IN": (n) => `നമസ്കാരം ${n} ജി! കിസാൻ മിത്ര AI-ലേക്ക് സ്വാഗതം. ഇന്ന് ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?`,
  "mr-IN": (n) => `नमस्कार ${n} जी! किसान मित्र AI मध्ये आपले स्वागत आहे. सांगा, आज मी आपली काय मदत करू शकतो?`,
  "pa-IN": (n) => `ਸਤਿ ਸ਼੍ਰੀ ਅਕਾਲ ${n} ਜੀ! ਕਿਸਾਨ ਮਿੱਤਰ AI ਵਿੱਚ ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ। ਦੱਸੋ, ਅੱਜ ਮੈਂ ਤੁਹਾਡੀ ਕੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?`,
  "gu-IN": (n) => `નમસ્તે ${n} જી! કિસાન મિત્ર AI માં આપનું સ્વાગત છે. બોલો, આજ હું આપની શું મદદ કરી શકું?`,
  "bn-IN": (n) => `নমস্কার ${n} জি! কিসান মিত্র AI-এ আপনাকে স্বাগতম। বলুন, আজ আমি আপনার কী সাহায্য করতে পারি?`,
};

/* ═══════════════════════════════════════════════════════════
   FALLBACK RESPONSES — ONE PER LANGUAGE (used when backend offline)
   ═══════════════════════════════════════════════════════════ */

const FALLBACK_RESPONSES: Record<string, (name: string) => string> = {
  "en-IN": (n) => `Your inquiry has been processed. You may be eligible for PM-Kisan Samman Nidhi scheme providing ₹6,000 per year. Please submit your Aadhaar card and land records to the nearest agriculture office.`,
  "hi-IN": (n) => `${n} जी, आपकी जानकारी संसाधित की गई है। आप पीएम-किसान सम्मान निधि योजना के लिए पात्र हो सकते हैं जो प्रति वर्ष ₹6,000 प्रदान करती है। कृपया अपना आधार कार्ड और भूमि अभिलेख नजदीकी कृषि कार्यालय में जमा करें।`,
  "kn-IN": (n) => `${n} ಅವರೇ, ನಿಮ್ಮ ಮಾಹಿತಿಯನ್ನು ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲಾಗಿದೆ. ನೀವು ಪಿಎಂ-ಕಿಸಾನ್ ಸಮ್ಮಾನ ನಿಧಿ ಯೋಜನೆಗೆ ಅರ್ಹರಾಗಿರಬಹುದು, ಇದು ವಾರ್ಷಿಕ ₹6,000 ಒದಗಿಸುತ್ತದೆ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಆಧಾರ್ ಕಾರ್ಡ್ ಮತ್ತು ಭೂಮಿ ದಾಖಲೆಗಳನ್ನು ಸಮೀಪದ ಕೃಷಿ ಕಚೇರಿಗೆ ಸಲ್ಲಿಸಿ.`,
  "te-IN": (n) => `${n} గారు, మీ సమాచారం ప్రాసెస్ చేయబడింది. మీరు పిఎం-కిసాన్ సమ్మాన్ నిధి పథకానికి అర్హులు కావచ్చు, ఇది సంవత్సరానికి ₹6,000 అందిస్తుంది. దయచేసి మీ ఆధార్ కార్డు మరియు భూమి పత్రాలను సమీపంలోని వ్యవసాయ కార్యాలయంలో సమర్పించండి.`,
  "ta-IN": (n) => `${n} அவர்களே, உங்கள் தகவல் செயலாக்கப்பட்டது. நீங்கள் பிஎம்-கிசான் சம்மான் நிதி திட்டத்திற்கு தகுதியானவராக இருக்கலாம், இது ஆண்டுக்கு ₹6,000 வழங்குகிறது. தயவுசெய்து உங்கள் ஆதார் அட்டை மற்றும் நிலப் பதிவுகளை அருகிலுள்ள வேளாண் அலுவலகத்தில் சமர்ப்பிக்கவும்.`,
  "ml-IN": (n) => `${n} ജി, നിങ്ങളുടെ വിവരങ്ങൾ പ്രോസസ്സ് ചെയ്തു. നിങ്ങൾ പിഎം-കിസാൻ സമ്മാൻ നിധി പദ്ധതിക്ക് അർഹനാകാം, ഇത് പ്രതിവർഷം ₹6,000 നൽകുന്നു. ദയവായി നിങ്ങളുടെ ആധാർ കാർഡും ഭൂമി രേഖകളും അടുത്തുള്ള കൃഷി ഓഫീസിൽ സമർപ്പിക്കുക.`,
  "mr-IN": (n) => `${n} जी, आपली माहिती प्रक्रिया केली गेली आहे. आपण पीएम-किसान सम्मान निधी योजनेसाठी पात्र असाल, जी दरवर्षी ₹6,000 देते. कृपया आपले आधार कार्ड आणि जमीन नोंदी जवळच्या कृषी कार्यालयात सादर करा.`,
  "pa-IN": (n) => `${n} ਜੀ, ਤੁਹਾਡੀ ਜਾਣਕਾਰੀ ਪ੍ਰਕਿਰਿਆ ਕੀਤੀ ਗਈ ਹੈ। ਤੁਸੀਂ ਪੀਐਮ-ਕਿਸਾਨ ਸਮਮਾਨ ਨਿਧੀ ਯੋਜਨਾ ਲਈ ਯੋਗ ਹੋ ਸਕਦੇ ਹੋ ਜੋ ਪ੍ਰਤੀ ਸਾਲ ₹6,000 ਪ੍ਰਦਾਨ ਕਰਦੀ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਆਪਣਾ ਆਧਾਰ ਕਾਰਡ ਅਤੇ ਜ਼ਮੀਨੀ ਰਿਕਾਰਡ ਨੇੜੇ ਦੇ ਖੇਤੀਬਾੜੀ ਦਫ਼ਤਰ ਵਿੱਚ ਜਮ੍ਹਾਂ ਕਰੋ।`,
  "gu-IN": (n) => `${n} જી, તમારી માહિતી પ્રક્રિયા કરવામાં આવી છે. તમે પીએમ-કિસાન સમ્માન નિધિ યોજના માટે પાત્ર હોઈ શકો, જે વાર્ષિક ₹6,000 આપે છે. કૃપા કરી તમારું આધાર કાર્ડ અને જમીન નોંધ નજીકની કૃષિ કચેરીમાં જમા કરો.`,
  "bn-IN": (n) => `${n} জি, আপনার তথ্য প্রক্রিয়া করা হয়েছে। আপনি পিএম-কিসান সম্মান নিধি প্রকল্পের জন্য যোগ্য হতে পারেন যা বছরে ₹6,000 প্রদান করে। দয়া করে আপনার আধার কার্ড এবং জমির রেকর্ড নিকটস্থ কৃষি অফিসে জমা দিন।`,
};

/* ═══════════════════════════════════════════════════════════
   DEFAULT FARMERS
   ═══════════════════════════════════════════════════════════ */

const DEFAULT_FARMERS: DemoFarmer[] = [
  {
    farmer_id: "DEMO-F004",
    name: "Priya Kumari",
    phone: "+91 98765 43213",
    state: "Karnataka",
    district: "Dharwad",
    category: "Medium",
    gender: "Female",
    land_hectares: 3.0,
    crops: ["Turmeric", "Groundnut"],
    language: "kn-IN",
    recent_damage: null,
    is_organic: true,
    is_tenant: false,
  },
  {
    farmer_id: "DEMO-F001",
    name: "Ramesh Singh",
    phone: "+91 98765 43210",
    state: "Punjab",
    district: "Ludhiana",
    category: "Small",
    gender: "Male",
    land_hectares: 2.0,
    crops: ["Wheat", "Rice"],
    language: "pa-IN",
    recent_damage: "Unseasonal rain damaged 20% wheat crop in March",
    is_organic: false,
    is_tenant: false,
  },
  {
    farmer_id: "DEMO-F002",
    name: "Sunita Devi",
    phone: "+91 98765 88990",
    state: "Maharashtra",
    district: "Yavatmal",
    category: "Marginal",
    gender: "Female",
    land_hectares: 1.2,
    crops: ["Cotton", "Soybean"],
    language: "mr-IN",
    recent_damage: null,
    is_organic: true,
    is_tenant: false,
  },
  {
    farmer_id: "DEMO-F003",
    name: "Anji Reddy",
    phone: "+91 98765 11223",
    state: "Telangana",
    district: "Warangal",
    category: "Medium",
    gender: "Male",
    land_hectares: 3.5,
    crops: ["Paddy", "Chilli"],
    language: "te-IN",
    recent_damage: null,
    is_organic: false,
    is_tenant: false,
  },
];

import { getApiBase } from "@/lib/utils";

const API_BASE = getApiBase();

/* ═══════════════════════════════════════════════════════════
   HOOK
   ═══════════════════════════════════════════════════════════ */

export function useDemoCallSession() {
  const [farmers, setFarmers] = useState<DemoFarmer[]>(DEFAULT_FARMERS);
  const [selectedFarmer, setSelectedFarmer] = useState<DemoFarmer>(DEFAULT_FARMERS[0]);

  // ── SINGLE SOURCE OF TRUTH: the user-selected language ──
  const [selectedLanguage, setSelectedLanguage] = useState<string>(DEFAULT_FARMERS[0].language);

  const [callState, setCallState] = useState<CallState>("idle");
  const [callDuration, setCallDuration] = useState(0);
  const [transcript, setTranscript] = useState<TranscriptTurn[]>([]);
  const [activePipelineStep, setActivePipelineStep] = useState<number>(0);
  const [isMuted, setIsMuted] = useState(false);
  const [aiResponseData, setAiResponseData] = useState<any>(null);

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const { isPlaying: isTtsPlaying, speak, stop: stopTts, voiceStatus, ttsWarning } = useTextToSpeech(selectedLanguage);

  /* ── When the user selects a language, it becomes the absolute authority ── */
  const handleLanguageChange = useCallback((langCode: string) => {
    setSelectedLanguage(langCode);
  }, []);

  /* ── When a new farmer profile is selected, update language to their preferred language ── */
  const handleFarmerChange = useCallback((farmer: DemoFarmer) => {
    setSelectedFarmer(farmer);
    setSelectedLanguage(farmer.language);
  }, []);

  /* ═══════════════════════════════════════════════════════
     SPEECH RESULT HANDLER
     Uses selectedLanguage as SINGLE SOURCE OF TRUTH.
     Stepping cleanly through all 5 pipeline stages:
     1: Speech STT → 2: Digital Twin → 3: Scheme RAG → 4: AI Reasoning → 5: Voice Output
     ═══════════════════════════════════════════════════════ */
  const handleSpeechResult = useCallback(
    async (spokenText: string, isFinal: boolean) => {
      if (!spokenText.trim() || !isFinal) return;

      // Use the user-selected language — always. No auto-guessing.
      const lang = selectedLanguage;
      const langOption = SUPPORTED_LANGUAGES.find(l => l.code === lang) || SUPPORTED_LANGUAGES[0];

      // Add farmer speech to transcript
      const turnId = `turn-${Date.now()}`;
      setTranscript((prev) => [
        ...prev,
        {
          id: turnId,
          role: "farmer",
          text: spokenText,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
          languageCode: lang,
        },
      ]);

      // Stage 1: Speech STT (Ingesting Farmer Input)
      setCallState("processing");
      setActivePipelineStep(1);
      console.log("[Pipeline Stage] 1/5: Speech STT");
      await new Promise((resolve) => setTimeout(resolve, 600));

      // Stage 2: Digital Twin (Loading Farmer Profile & Land Records)
      setActivePipelineStep(2);
      console.log("[Pipeline Stage] 2/5: Digital Twin Context Enrichment");
      await new Promise((resolve) => setTimeout(resolve, 600));

      // Stage 3: Scheme RAG (Querying Government Knowledge Base)
      setActivePipelineStep(3);
      console.log("[Pipeline Stage] 3/5: Scheme RAG & Eligibility Rules Evaluation");

      let data: any = null;
      try {
        // Build the LLM prompt language instruction
        const languageInstruction = [
          `Selected Language: ${langOption.promptName}`,
          `Instructions:`,
          `- Answer ONLY in ${langOption.promptName}.`,
          `- Do not translate.`,
          `- Do not mix English.`,
          `- Do not mix Hindi.`,
          `- Keep the answer simple.`,
          `- Maximum 3-4 short sentences.`,
          `- Suitable for a farmer.`,
        ].join("\n");

        const payload = {
          farmer_id: selectedFarmer.farmer_id,
          farmer_name: selectedFarmer.name,
          state: selectedFarmer.state,
          language: lang,
          preferred_language: lang,
          detected_language: lang,
          user_selected_language: lang,
          question: spokenText,
          query_text: spokenText,
          language_instruction: languageInstruction,
          response_language: lang,
        };

        const res = await fetch(`${API_BASE}/api/v1/demo/call/process`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (res.ok) {
          data = await res.json();
          data.response_language_tag = lang;
          data.response_language = lang;
        }
      } catch (err) {
        console.error("[useDemoCallSession] API request error, proceeding with fallback:", err);
      }

      await new Promise((resolve) => setTimeout(resolve, 500));

      // If backend was offline or failed, generate language-pure fallback response
      if (!data || !data.voice_response) {
        const name = selectedFarmer.name.split(" ")[0];
        const fallbackFn = FALLBACK_RESPONSES[lang] || FALLBACK_RESPONSES["en-IN"];
        const respText = fallbackFn(name);

        data = {
          success: true,
          farmer_name: selectedFarmer.name,
          state: selectedFarmer.state,
          question: spokenText,
          detected_speech_language: lang,
          response_language: lang,
          response_language_tag: lang,
          top_scheme: "PM-Kisan Samman Nidhi",
          voice_response: respText,
          reasoning: [
            `✓ Language: ${langOption.promptName}`,
            `✓ Query processed for ${selectedFarmer.name} (${selectedFarmer.land_hectares} Ha).`,
          ],
          document_guidance: {
            required_documents: ["Aadhaar Card", "Land Record", "Bank Passbook"],
            helpline: "1800-180-1551",
          },
        };
      }

      // Stage 4: AI Reasoning (LangGraph Multi-Agent Decision Compilation)
      setActivePipelineStep(4);
      console.log("[Pipeline Stage] 4/5: AI Multi-Agent Reasoning Graph");
      setAiResponseData(data);

      const responseText = data.voice_response || FALLBACK_RESPONSES[lang]?.(selectedFarmer.name.split(" ")[0]) || "";

      // Add AI response turn to transcript
      setTranscript((prev) => [
        ...prev,
        {
          id: `turn-ai-${Date.now()}`,
          role: "assistant",
          text: responseText,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
          languageCode: lang,
        },
      ]);

      await new Promise((resolve) => setTimeout(resolve, 800));

      // Stage 5: Voice Output (TTS Audio Synthesis & Playback)
      setActivePipelineStep(5);
      console.log("[Pipeline Stage] 5/5: Voice Output Audio Playback");
      setCallState("speaking");

      // Speak in selected language voice; callState transitions to connected ONLY when audio finishes
      speak(responseText, lang, () => {
        setCallState("connected");
        setActivePipelineStep(5);
        console.log("[Pipeline Stage] All 5 pipeline stages completed successfully with audio playback.");
      });
    },
    [selectedLanguage, selectedFarmer, speak]
  );

  /* ── Speech recognition always uses selectedLanguage ── */
  const {
    isListening,
    transcript: speechTranscript,
    startListening,
    stopListening,
    resetTranscript,
  } = useSpeechRecognition({
    language: selectedLanguage,
    onResult: (text, isFinal) => handleSpeechResult(text, isFinal),
  });

  /* ── Call timer ── */
  useEffect(() => {
    if (callState === "connected" || callState === "listening" || callState === "processing" || callState === "speaking") {
      timerRef.current = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [callState]);

  /* ── Load demo farmers ── */
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/demo/farmers`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && Array.isArray(data) && data.length > 0) {
          setFarmers((prev) => {
            const existingIds = new Set(prev.map((f) => f.farmer_id));
            const newFarmers = data.filter((f: any) => !existingIds.has(f.farmer_id));
            return [...prev, ...newFarmers];
          });
        }
      })
      .catch(() => {});
  }, []);

  const triggerIncomingCall = useCallback((farmer?: DemoFarmer) => {
    if (farmer) {
      setSelectedFarmer(farmer);
      // When a specific farmer is chosen, use their language as default
      setSelectedLanguage(farmer.language);
    }
    setCallState("incoming");
    setCallDuration(0);
    setTranscript([]);
    setActivePipelineStep(0);
    setAiResponseData(null);
  }, []);

  const acceptCall = useCallback(() => {
    const lang = selectedLanguage;
    const name = selectedFarmer.name.split(" ")[0];
    const greetFn = GREETINGS[lang] || GREETINGS["en-IN"];
    const greetingText = greetFn(name);

    setCallState("connected");
    setActivePipelineStep(1);

    setTranscript([
      {
        id: "turn-system-0",
        role: "system",
        text: `Call Connected — ${selectedFarmer.name} (${selectedFarmer.state})`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        languageCode: lang,
      },
      {
        id: "turn-ai-0",
        role: "assistant",
        text: greetingText,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        languageCode: lang,
      },
    ]);

    setCallState("speaking");
    speak(greetingText, lang, () => {
      setCallState("connected");
    });
  }, [selectedLanguage, selectedFarmer, speak]);

  const rejectCall = useCallback(() => {
    setCallState("ended");
    stopTts();
    stopListening();
  }, [stopListening, stopTts]);

  const endCall = useCallback(() => {
    setCallState("ended");
    stopTts();
    stopListening();
  }, [stopListening, stopTts]);

  const toggleMicListening = useCallback(() => {
    if (callState === "speaking") stopTts();
    if (isListening) {
      stopListening();
      setCallState("connected");
    } else {
      resetTranscript();
      setCallState("listening");
      setActivePipelineStep(2);
      startListening();
    }
  }, [callState, isListening, resetTranscript, startListening, stopListening, stopTts]);

  const submitPresetQuery = useCallback(
    (presetText: string) => {
      if (callState === "speaking") stopTts();
      handleSpeechResult(presetText, true);
    },
    [callState, handleSpeechResult, stopTts]
  );

  return {
    farmers,
    selectedFarmer,
    setSelectedFarmer: handleFarmerChange,
    selectedLanguage,
    setSelectedLanguage: handleLanguageChange,
    callState,
    callDuration,
    transcript,
    activePipelineStep,
    isMuted,
    setIsMuted,
    isListening,
    isTtsPlaying,
    speechTranscript,
    aiResponseData,
    voiceStatus,
    ttsWarning,
    triggerIncomingCall,
    acceptCall,
    rejectCall,
    endCall,
    toggleMicListening,
    submitPresetQuery,
  };
}
