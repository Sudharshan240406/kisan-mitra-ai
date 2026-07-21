"""
Kisan Mitra AI — Language Detector
=====================================
Unicode script-based language detection for Indian languages.
Works fully offline — zero API calls, deterministic, sub-millisecond.

Detects:
  - hi  (Hindi   — Devanagari)
  - kn  (Kannada — Kannada script)
  - te  (Telugu  — Telugu script)
  - ta  (Tamil   — Tamil script)
  - pa  (Punjabi — Gurmukhi script)
  - mr  (Marathi — Devanagari, shared with Hindi; detected by vocabulary)
  - en  (English — Latin script)
  - mixed (multiple scripts in one utterance)

Stores detected language preference to Digital Twin Memory (ARM).
"""
from __future__ import annotations

import logging
import unicodedata

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.voice.language_detector")


# ---------------------------------------------------------------------------
# Unicode Script Ranges for Indian Languages
# ---------------------------------------------------------------------------

# Devanagari: U+0900–U+097F (Hindi, Marathi, Sanskrit, Nepali)
_DEVANAGARI_RANGE = (0x0900, 0x097F)
# Bengali: U+0980–U+09FF
_BENGALI_RANGE = (0x0980, 0x09FF)
# Gurmukhi: U+0A00–U+0A7F (Punjabi)
_GURMUKHI_RANGE = (0x0A00, 0x0A7F)
# Gujarati: U+0A80–U+0AFF
_GUJARATI_RANGE = (0x0A80, 0x0AFF)
# Oriya: U+0B00–U+0B7F
_ORIYA_RANGE = (0x0B00, 0x0B7F)
# Tamil: U+0B80–U+0BFF
_TAMIL_RANGE = (0x0B80, 0x0BFF)
# Telugu: U+0C00–U+0C7F
_TELUGU_RANGE = (0x0C00, 0x0C7F)
# Kannada: U+0C80–U+0CFF
_KANNADA_RANGE = (0x0C80, 0x0CFF)
# Malayalam: U+0D00–U+0D7F
_MALAYALAM_RANGE = (0x0D00, 0x0D7F)

# Marathi common words (Devanagari; differentiated from Hindi)
_MARATHI_MARKERS = frozenset(["माझे", "तुमचे", "शेती", "पेरणी", "कापूस", "मराठी"])
_HINDI_MARKERS = frozenset(["मेरा", "आपका", "किसान", "खेती", "फसल", "हिंदी"])


# ---------------------------------------------------------------------------
# DetectionResult
# ---------------------------------------------------------------------------

class DetectionResult(BaseModel):
    """Output of language detection."""
    language: str = Field(..., description="ISO 639-1 language code.")
    confidence: float = Field(..., description="Detection confidence (0.0–1.0).")
    script: str = Field(..., description="Detected Unicode script name.")
    is_mixed: bool = Field(default=False, description="True if multiple scripts detected.")
    char_distribution: dict[str, int] = Field(
        default_factory=dict, description="Script char count breakdown."
    )


# ---------------------------------------------------------------------------
# LanguageDetector
# ---------------------------------------------------------------------------

class LanguageDetector:
    """
    Unicode script-based language detector for Indian languages.
    Zero external dependencies, deterministic, sub-millisecond latency.

    Detection algorithm:
      1. Count characters per Unicode script block.
      2. Determine dominant script.
      3. If Devanagari dominant, apply Hindi/Marathi word-marker disambiguation.
      4. If multiple scripts detected (mixed), flag as mixed.
      5. Return DetectionResult with confidence proportional to char dominance.
    """

    LANG_MAP: dict[str, str] = {
        "Devanagari": "hi",
        "Gurmukhi": "pa",
        "Tamil": "ta",
        "Telugu": "te",
        "Kannada": "kn",
        "Latin": "en",
        "Bengali": "bn",
        "Gujarati": "gu",
        "Oriya": "or",
        "Malayalam": "ml",
    }

    def detect(self, text: str) -> DetectionResult:
        """
        Detect the dominant language from text using Unicode script analysis.
        """
        if not text or not text.strip():
            return DetectionResult(
                language="hi", confidence=0.0, script="Unknown",
                is_mixed=False, char_distribution={}
            )

        script_counts: dict[str, int] = {}
        total_alpha = 0

        for char in text:
            if not char.isalpha():
                continue
            total_alpha += 1
            cp = ord(char)
            script = self._classify_codepoint(cp)
            script_counts[script] = script_counts.get(script, 0) + 1

        if not script_counts or total_alpha == 0:
            return DetectionResult(
                language="en", confidence=0.5, script="Unknown",
                is_mixed=False, char_distribution={}
            )

        # Dominant script
        dominant_script = max(script_counts, key=lambda s: script_counts[s])
        dominant_count = script_counts[dominant_script]
        confidence = round(dominant_count / total_alpha, 4)

        # Mixed language detection
        non_trivial = [s for s, c in script_counts.items() if c / total_alpha > 0.15]
        is_mixed = len(non_trivial) > 1

        # Map script to language
        lang = self.LANG_MAP.get(dominant_script, "hi")

        # Devanagari: Hindi vs Marathi disambiguation
        if lang == "hi":
            lang = self._disambiguate_devanagari(text)

        logger.debug(
            f"[LanguageDetector] text='{text[:30]}...' → lang={lang}, "
            f"script={dominant_script}, conf={confidence:.2f}, mixed={is_mixed}"
        )
        return DetectionResult(
            language=lang,
            confidence=confidence,
            script=dominant_script,
            is_mixed=is_mixed,
            char_distribution=script_counts,
        )

    def _classify_codepoint(self, cp: int) -> str:
        """Maps a Unicode codepoint to a script name."""
        if _DEVANAGARI_RANGE[0] <= cp <= _DEVANAGARI_RANGE[1]:
            return "Devanagari"
        if _GURMUKHI_RANGE[0] <= cp <= _GURMUKHI_RANGE[1]:
            return "Gurmukhi"
        if _TAMIL_RANGE[0] <= cp <= _TAMIL_RANGE[1]:
            return "Tamil"
        if _TELUGU_RANGE[0] <= cp <= _TELUGU_RANGE[1]:
            return "Telugu"
        if _KANNADA_RANGE[0] <= cp <= _KANNADA_RANGE[1]:
            return "Kannada"
        if _BENGALI_RANGE[0] <= cp <= _BENGALI_RANGE[1]:
            return "Bengali"
        if _GUJARATI_RANGE[0] <= cp <= _GUJARATI_RANGE[1]:
            return "Gujarati"
        if _MALAYALAM_RANGE[0] <= cp <= _MALAYALAM_RANGE[1]:
            return "Malayalam"
        if _ORIYA_RANGE[0] <= cp <= _ORIYA_RANGE[1]:
            return "Oriya"
        # Latin: ASCII a-z and extended Latin
        try:
            name = unicodedata.name(chr(cp), "")
            if "LATIN" in name:
                return "Latin"
        except (ValueError, TypeError):
            pass
        if 0x0041 <= cp <= 0x007A:
            return "Latin"
        return "Unknown"

    def _disambiguate_devanagari(self, text: str) -> str:
        """Distinguish Hindi from Marathi using vocabulary markers."""
        marathi_hits = sum(1 for w in _MARATHI_MARKERS if w in text)
        hindi_hits = sum(1 for w in _HINDI_MARKERS if w in text)
        if marathi_hits > hindi_hits:
            return "mr"
        return "hi"

    def detect_batch(self, texts: list[str]) -> list[DetectionResult]:
        """Detect language for a list of transcripts."""
        return [self.detect(t) for t in texts]

    def most_common_language(self, texts: list[str]) -> str:
        """Returns the most frequently detected language across a batch."""
        results = self.detect_batch(texts)
        counts: dict[str, int] = {}
        for r in results:
            counts[r.language] = counts.get(r.language, 0) + 1
        return max(counts, key=lambda k: counts[k]) if counts else "hi"


# ---------------------------------------------------------------------------
# Language code → IVR label
# ---------------------------------------------------------------------------

LANGUAGE_NAMES: dict[str, str] = {
    "hi": "हिंदी",
    "en": "English",
    "kn": "ಕನ್ನಡ",
    "te": "తెలుగు",
    "ta": "தமிழ்",
    "pa": "ਪੰਜਾਬੀ",
    "mr": "मराठी",
    "bn": "বাংলা",
    "gu": "ગુજરાતી",
    "ml": "മലയാളം",
}


def language_display_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code.upper())
