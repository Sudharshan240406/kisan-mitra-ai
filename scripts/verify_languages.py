import asyncio
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.api.v1.demo import process_demo_voice_query, DemoVoiceQueryRequest
from app.core.container import Container
from app.core.config import settings

async def verify_language_flow():
    container = Container(settings)
    
    test_cases = [
        # Language 1: Kannada (kn)
        {
            "lang": "kn",
            "lang_name": "Kannada",
            "tag": "kn-IN",
            "q1": "ನನ್ನ ಬೆಳೆಗೆ ಮಳೆಯಿಂದ ಹಾನಿಯಾಗಿದೆ, ಪರಿಹಾರ ಹೇಗೆ ಸಿಗುತ್ತದೆ?",
            "q2": "ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಯ ಹಣ ಎಂದಿಗೆ ಬರುತ್ತದೆ?",
        },
        # Language 2: Telugu (te)
        {
            "lang": "te",
            "lang_name": "Telugu",
            "tag": "te-IN",
            "q1": "నా పంట వర్షాల వల్ల పాడైపోయింది, ఏ పథకం వర్తిస్తుంది?",
            "q2": "పీఎం కిసాన్ పథకానికి ఏ పత్రాలు కావాలి?",
        },
        # Language 3: English (en)
        {
            "lang": "en",
            "lang_name": "English",
            "tag": "en-IN",
            "q1": "How do I claim crop insurance after heavy rainfall?",
            "q2": "What are the eligibility criteria for PM-Kisan scheme?",
        }
    ]

    print("============================================================")
    print("STARTING DEMO MODE WALKTHROUGH (Kannada, Telugu, English)")
    print("============================================================\n")

    for tc in test_cases:
        lang = tc["lang"]
        print(f"── Testing Language: {tc['lang_name']} ({lang}) ──")

        # Query 1
        req1 = DemoVoiceQueryRequest(
            farmer_id="DEMO-F001",
            user_selected_language=lang,
            question=tc["q1"],
        )
        res1 = await process_demo_voice_query(req1, container)

        # Query 2
        req2 = DemoVoiceQueryRequest(
            farmer_id="DEMO-F001",
            user_selected_language=lang,
            question=tc["q2"],
        )
        res2 = await process_demo_voice_query(req2, container)

        ans1 = res1["voice_response"]
        ans2 = res2["voice_response"]

        print(f"  Q1: {tc['q1']}")
        print(f"  A1: {ans1[:120]}...\n")
        print(f"  Q2: {tc['q2']}")
        print(f"  A2: {ans2[:120]}...\n")

        # Verifications
        assert res1["success"] is True, "Q1 failed"
        assert res2["success"] is True, "Q2 failed"

        # 1. Different question -> different answer
        assert ans1 != ans2, f"FAILED: Answers for Q1 and Q2 are identical in {tc['lang_name']}"
        print(f"  ✓ Different question → different answer: PASSED")

        # 2. Response language tag matches selected language
        assert res1["lang_code"] == lang, f"FAILED: Target language code mismatch. Expected {lang}, got {res1['lang_code']}"
        assert res1["response_language"] == tc["lang_name"], f"FAILED: Target language name mismatch."
        print(f"  ✓ Response language matches selected language ({tc['lang_name']}): PASSED")

        # 3. TTS voice tag matches selected language
        assert res1["response_language_tag"] == tc["tag"], f"FAILED: TTS tag mismatch. Expected {tc['tag']}, got {res1['response_language_tag']}"
        print(f"  ✓ TTS voice tag matches selected language ({tc['tag']}): PASSED")

        # 4. No mock/debug text in response
        assert "mock" not in ans1.lower(), "FAILED: Mock text found in A1"
        assert "debug" not in ans1.lower(), "FAILED: Debug text found in A1"
        assert "mock" not in ans2.lower(), "FAILED: Mock text found in A2"
        assert "debug" not in ans2.lower(), "FAILED: Debug text found in A2"
        print(f"  ✓ Zero mock/debug text: PASSED\n")

    print("============================================================")
    print("ALL 3-LANGUAGE DEMO MODE WALKTHROUGH VERIFICATIONS PASSED!")
    print("============================================================")

if __name__ == "__main__":
    asyncio.run(verify_language_flow())
