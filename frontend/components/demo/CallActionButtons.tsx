"use client";

import React from "react";
import { motion } from "framer-motion";
import { Phone, PhoneOff, Mic, MicOff, Sparkles } from "lucide-react";
import { CallState } from "@/hooks/useDemoCallSession";

interface CallActionButtonsProps {
  callState: CallState;
  onAccept: () => void;
  onReject: () => void;
  onEnd: () => void;
  onToggleMic: () => void;
  onPresetQuery: (text: string) => void;
  isListening: boolean;
  isMuted: boolean;
  onToggleMute: () => void;
  language?: string;
}

/* ════════════════════════════════════════════════════════════
   SUGGESTED QUESTIONS — All 10 languages, 3 per language.
   These must exactly match the selected language.
   NO English fallback for Indian languages.
   ════════════════════════════════════════════════════════════ */

const SUGGESTED_QUESTIONS: Record<string, string[]> = {
  "en-IN": [
    "My crop was damaged by heavy rain. What help is available?",
    "What are the eligibility criteria for PM Kisan Samman Nidhi?",
    "What documents are needed for PM Fasal Bima Yojana?",
    "Which fertilizer is recommended for wheat crop?",
    "How do I test my soil health?",
    "What is the market price for Paddy today?",
    "How can I set up drip irrigation?",
    "How to control yellow rust in crops?",
  ],
  "hi-IN": [
    "मेरी फसल बारिश से खराब हो गई है, मुआवजा कैसे मिलेगा?",
    "पीएम किसान सम्मान निधि की पात्रता क्या है?",
    "फसल बीमा का दावा करने के लिए कौन से दस्तावेज़ चाहिए?",
    "गेहूं की फसल के लिए कौन सी खाद अच्छी है?",
    "मिट्टी परीक्षण कैसे करवाएं?",
    "आज मंडी में गेहूं का भाव क्या है?",
    "ड्रिप सिंचाई के लिए सरकारी सब्सिडी कितनी है?",
    "फसल में कीट नियंत्रण कैसे करें?",
  ],
  "kn-IN": [
    "ಮಳೆಯಿಂದ ನನ್ನ ಬೆಳೆ ಹಾನಿಯಾಗಿದೆ, ಪರಿಹಾರ ಹೇಗೆ ಸಿಗುತ್ತದೆ?",
    "ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಯ ಹಣ ಪಡೆಯಲು ಯಾರು ಅರ್ಹರು?",
    "ಬೆಳೆ ವಿಮೆ ಪಡೆದುಕೊಳ್ಳಲು ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
    "ಗೋಧಿ ಮತ್ತು ಬತ್ತಕ್ಕೆ ಯಾವ ರಸಗೊಬ್ಬರ ಸೂಕ್ತ?",
    "ಮಣ್ಣಿನ ಆರೋಗ್ಯ ಪರೀಕ್ಷೆ ಎಲ್ಲಿ ಮಾಡಿಸಬೇಕು?",
    "ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ ಇಂದಿನ ಬೆಳೆ ಬೆಲೆ ಎಷ್ಟು?",
    "ಹನಿ ನೀರಾವರಿಗೆ ಸರ್ಕಾರಿ ಸಬ್ಸಿಡಿ ಇದೆಯೇ?",
    "ಬೆಳೆಯಲ್ಲಿ ಕೀಟ ಬಾಧೆ ನಿಯಂತ್ರಿಸುವುದು ಹೇಗೆ?",
  ],
  "te-IN": [
    "వర్షాల వల్ల నా పంట పాడైపోయింది, పరిహారం ఎలా వస్తుంది?",
    "పీఎం కిసాన్ పథకానికి ఎవరు అర్హులు?",
    "పంట బీమా క్లెయిమ్ చేయడానికి ఏ పత్రాలు కావాలి?",
    "వరి పంటకు ఏ ఎరువు వాడాలి?",
    "నేల పరీక్ష ఎలా చేయించుకోవాలి?",
    "ఈరోజు మార్కెట్లో ధాన్యం ధర ఎంత ఉందో చెప్పండి?",
    "బిందు సేద్యం (డ్రిప్)కి ప్రభుత్వ రాయితీ ఉందా?",
    "పంట తెగుళ్ల నివారణ ఎలా చేయాలి?",
  ],
  "ta-IN": [
    "மழையால் பயிர் சேதமடைந்தது, இழப்பீடு பெறுவது எப்படி?",
    "பிஎம் கிசான் திட்டத்தின் தகுதிகள் யாவை?",
    "பயிர் காப்பீட்டுக்கு என்ன ஆவணங்கள் தேவை?",
    "நெல் பயிருக்கு என்ன உரம் பயன்படுத்த வேண்டும்?",
    "மண் பரிசோதனை எங்கு செய்வது?",
    "இன்றைய சந்தை விலை என்ன?",
    "சொட்டு நீர் பாசனத்திற்கு மானியம் உள்ளதா?",
    "பயிர்களில் பூச்சி கட்டுப்பாடு செய்வது எப்படி?",
  ],
  "ml-IN": [
    "മഴ മൂലം വിള നശിച്ചു, നഷ്ടപരിഹാരം എങ്ങനെ ലഭിക്കും?",
    "പിഎം കിസാൻ പദ്ധതിയുടെ യോഗ്യത എന്താണ്?",
    "വിള ഇൻഷുറൻസിന് ഏത് രേഖകൾ വേണം?",
    "നെൽകൃഷിക്ക് ഏത് വളമാണ് നല്ലത്?",
    "മണ്ണ് പരിശോധന എങ്ങനെ നടത്താം?",
    "ഇന്നത്തെ വിപണി വില എത്രയാണ്?",
    "തുള്ളി നനയ്ക്കലിന് (ഡ്രിപ്പ്) സബ്സിഡി ഉണ്ടോ?",
    "കീട നിയന്ത്രണം എങ്ങനെ നടത്താം?",
  ],
  "mr-IN": [
    "पावसामुळे पिकाचे नुकसान झाले, भरपाई कशी मिळेल?",
    "पीएम किसान सन्मान निधीसाठी पात्रता काय आहे?",
    "पीक विम्यासाठी कोणती कागदपत्रे लागतात?",
    "गव्हाच्या पिकासाठी कोणते खत वापरावे?",
    "माती परीक्षण कसे करावे?",
    "आजचा शेतमालाचा बाजार भाव काय आहे?",
    "ठिबक सिंचनासाठी शासकीय अनुदान किती मिळते?",
    "पिकावरील कीड नियंत्रण कसे करावे?",
  ],
  "pa-IN": [
    "ਮੀਂਹ ਨਾਲ ਫ਼ਸਲ ਦਾ ਨੁਕਸਾਨ ਹੋਇਆ, ਮੁਆਵਜ਼ਾ ਕਿਵੇਂ ਮਿਲੇਗਾ?",
    "ਪੀਐਮ ਕਿਸਾਨ ਯੋਜਨਾ ਲਈ ਕੀ ਯੋਗਤਾ ਹੈ?",
    "ਫ਼ਸਲ ਬੀਮੇ ਲਈ ਕਿਹੜੇ ਦਸਤਾਵੇਜ਼ ਚਾਹੀਦੇ ਹਨ?",
    "ਕਣਕ ਦੀ ਫ਼ਸਲ ਲਈ ਕਿਹੜੀ ਖਾਦ ਵਧੀਆ ਹੈ?",
    "ਮਿੱਟੀ ਦੀ ਜਾਂਚ ਕਿਵੇਂ ਕਰਵਾਈਏ?",
    "ਅੱਜ ਮੰਡੀ ਵਿੱਚ ਝੋਨੇ ਅਤੇ ਕਣਕ ਦਾ ਭਾਅ ਕੀ ਹੈ?",
    "ਟਿੱਪਕ ਸਿੰਚਾਈ ਲਈ ਸਰਕਾਰੀ ਸਬਸਿਡੀ ਮਿਲਦੀ ਹੈ?",
    "ਫ਼ਸਲ ਦੇ ਕੀੜਿਆਂ ਦੀ ਰੋਕਥਾਮ ਕਿਵੇਂ ਕਰੀਏ?",
  ],
  "gu-IN": [
    "વરસાદથી પાક નુકસાન થયું, વળતર કેવી રીતે મળશે?",
    "પીએમ કિસાન યોજનાની પાત્રતા શું છે?",
    "પાક વીમા માટે કયા દસ્તાવેજો જોઈએ?",
    "ઘઉંના પાક માટે કયું ખાતર સારું?",
    "માટી પરીક્ષણ કેવી રીતે કરાવવું?",
    "આજે મંડીમાં પાકના ભાવ શું છે?",
    "ટપક સિંચાઈ માટે સરકારી સબસીડી મળશે?",
    "પાકમાં જીવાત નિયંત્રણ કેવી રીતે કરવું?",
  ],
  "bn-IN": [
    "বৃষ্টিতে ফসল নষ্ট হয়েছে, ক্ষতিপূরণ কীভাবে পাব?",
    "পিএম কিসান সম্মান নিধির যোগ্যতা কী?",
    "ফসল বিমার জন্য কী কী কাগজপত্র লাগবে?",
    "ধান ও গম ফসলের জন্য কোন সার সেরা?",
    "মাটি পরীক্ষা কীভাবে করাব?",
    "আজকের বাজারে ধানের দাম কত?",
    "বিন্দু সেচের (ড্রিপ) জন্য সরকারি ভরতুকি পাওয়া যাবে?",
    "ফসলের পোકા দমনে কী উপায়?",
  ],
};

export function CallActionButtons({
  callState,
  onAccept,
  onReject,
  onEnd,
  onToggleMic,
  onPresetQuery,
  isListening,
  isMuted,
  onToggleMute,
  language = "en-IN",
}: CallActionButtonsProps) {
  const isConnected =
    callState === "connected" ||
    callState === "listening" ||
    callState === "processing" ||
    callState === "speaking";

  // Get questions for the selected language — guaranteed to exist
  const questions =
    SUGGESTED_QUESTIONS[language] ??
    SUGGESTED_QUESTIONS["en-IN"];

  return (
    <div className="mt-4 space-y-3">

      {/* Suggested demo questions — only in the selected language */}
      {isConnected && (
        <div className="space-y-1.5">
          <div className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-cyan-400" />
            <span className="uppercase tracking-wider">Sample Questions:</span>
          </div>
          <div className="flex flex-col gap-1.5">
            {questions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => onPresetQuery(q)}
                disabled={callState === "processing"}
                className="text-[12px] bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 hover:border-emerald-500/50 text-slate-200 px-3 py-1.5 rounded-xl transition-all text-left disabled:opacity-50 cursor-pointer leading-snug"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main call controls */}
      <div className="flex items-center justify-center gap-4 pt-2">
        {callState === "incoming" ? (
          <>
            {/* Reject */}
            <motion.button
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.95 }}
              onClick={onReject}
              className="flex h-14 w-14 items-center justify-center rounded-full bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-900/50 border border-rose-400/30"
              title="Reject Call"
            >
              <PhoneOff className="w-6 h-6 rotate-[135deg]" />
            </motion.button>

            {/* Accept */}
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={onAccept}
              className="relative flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500 hover:bg-emerald-400 text-white shadow-xl shadow-emerald-900/60 border border-emerald-300"
              title="Accept Call"
            >
              <span className="absolute -inset-2 animate-ping rounded-full bg-emerald-400/40 opacity-75" />
              <Phone className="w-7 h-7" />
            </motion.button>
          </>
        ) : isConnected ? (
          <>
            {/* Toggle Mute */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onToggleMute}
              className={`flex h-12 w-12 items-center justify-center rounded-full border text-xs transition-all ${
                isMuted
                  ? "bg-amber-950/80 border-amber-500 text-amber-400"
                  : "bg-slate-900/90 border-slate-700 text-slate-300 hover:bg-slate-800"
              }`}
              title={isMuted ? "Unmute" : "Mute"}
            >
              {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </motion.button>

            {/* Speak / Listening toggle */}
            <motion.button
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.95 }}
              onClick={onToggleMic}
              disabled={callState === "processing"}
              className={`flex h-14 px-5 items-center justify-center gap-2 rounded-full border text-sm font-semibold transition-all shadow-lg ${
                isListening
                  ? "bg-cyan-500 hover:bg-cyan-400 text-slate-950 border-cyan-300 shadow-cyan-900/50 animate-pulse"
                  : "bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-400 shadow-emerald-950/60"
              } disabled:opacity-50`}
            >
              <Mic className="w-5 h-5" />
              <span>{isListening ? "Listening..." : "Speak into Mic"}</span>
            </motion.button>

            {/* End Call */}
            <motion.button
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.95 }}
              onClick={onEnd}
              className="flex h-12 w-12 items-center justify-center rounded-full bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-950/60 border border-rose-400/30"
              title="End Call"
            >
              <PhoneOff className="w-5 h-5" />
            </motion.button>
          </>
        ) : (
          /* Ended state */
          <button
            onClick={onAccept}
            className="flex items-center gap-2 px-6 py-2.5 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg"
          >
            <Phone className="w-4 h-4" />
            Restart Call Simulation
          </button>
        )}
      </div>
    </div>
  );
}
