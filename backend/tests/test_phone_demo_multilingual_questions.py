import pytest
import asyncio
from app.core.container import Container
from app.api.v1.demo import simulate_call, SimulateCallRequest


@pytest.mark.asyncio
async def test_simulate_call_8_combinations_matrix():
    container = Container()
    farmer_id = "DEMO-F001"  # Ramesh Singh (Punjab)

    questions = [
        ("market_price", "What is the current mandi rate for wheat in Punjab?"),
        ("weather", "What is the weather forecast for Ludhiana today?"),
        ("disease", "My wheat crop has yellow rust spots, what should I spray?"),
        ("scheme", "What government schemes am I eligible for?"),
    ]

    languages = ["hi", "kn"]

    results_matrix = {}

    for q_key, q_text in questions:
        for lang in languages:
            req = SimulateCallRequest(question=q_text, language=lang)
            res = await simulate_call(farmer_id=farmer_id, request=req, container=container)

            assert res["success"] is True
            transcript = res["transcript"]
            voice_response = res["voice_response"]

            # Extract farmer speech turn from transcript
            farmer_turns = [t for t in transcript if t["role"] == "farmer"]
            assert len(farmer_turns) > 0
            farmer_speech = farmer_turns[0]["text"]

            results_matrix[(q_key, lang)] = {
                "question": q_text,
                "language": lang,
                "farmer_speech": farmer_speech,
                "voice_response": voice_response,
                "eligible_count": res.get("eligible_count", 0),
            }

    # 1. Verify that all 8 farmer speech lines are unique across question+lang pairs
    farmer_speeches = [v["farmer_speech"] for v in results_matrix.values()]
    assert len(set(farmer_speeches)) == 8, f"Expected 8 unique farmer speech lines, got {len(set(farmer_speeches))}"

    # 2. Verify that voice responses vary appropriately across questions
    voice_responses = [v["voice_response"] for v in results_matrix.values()]
    assert len(set(voice_responses)) >= 6, "Voice responses must differ per question and language"

    # 3. Verify scheme eligibility flow works for scheme questions
    scheme_hi = results_matrix[("scheme", "hi")]
    assert scheme_hi["eligible_count"] > 0

    print("\n" + "="*80)
    print("PHONE DEMO MULTILINGUAL MATRIX RESULTS (8 COMBINATIONS):")
    print("="*80)
    for (q_key, lang), data in results_matrix.items():
        print(f"[{q_key.upper()} | Language: {lang}]")
        print(f"  Farmer Question : {data['question']}")
        print(f"  Farmer Speaks   : {data['farmer_speech'].encode('ascii', errors='replace').decode('ascii')}")
        print(f"  AI Voice Output : {data['voice_response'].encode('ascii', errors='replace').decode('ascii')}")
        print("-" * 80)
