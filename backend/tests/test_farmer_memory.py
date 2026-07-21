import time

from app.memory.conversation_memory import ConversationTurn
from app.memory.memory_engine import FarmerMemoryEngine
from app.memory.memory_manager import MemoryManager
from app.memory.vector_memory import VectorMemoryIndex


def test_memory_engine_save_and_retrieve():
    engine = FarmerMemoryEngine()
    farmer_id = "farmer_test_id"
    engine.delete_memory(farmer_id)

    # Save conversation turn
    engine.save_memory(
        farmer_id=farmer_id,
        question="How to grow organic wheat in Punjab?",
        intent="Government Scheme",
        response="Use PM-Kisan portal advice.",
        confidence=0.98,
        execution_id="EXEC-999",
        recommended_schemes=["pm-kisan"],
        documents_requested=["Aadhaar", "Land Records"]
    )

    # Retrieve memories
    memory = engine.retrieve_memory(farmer_id)
    assert memory["profile"]["farmer_id"] == farmer_id
    assert len(memory["history"]) == 1
    assert memory["history"][0]["question"] == "How to grow organic wheat in Punjab?"
    assert "pm-kisan" in memory["recommendations"]["recommended_schemes"]
    assert "Aadhaar" in memory["recommendations"]["documents_requested"]
    assert "Punjab" in memory["summary"] or "wheat" in memory["summary"]

def test_vector_memory_semantic_search():
    index = VectorMemoryIndex()
    index.add_document("PM-Kisan organic subsidy guidelines", {"id": "doc1", "farmer_id": "test_f"})
    index.add_document("Monsoon rain forecasts in Ludhiana", {"id": "doc2", "farmer_id": "test_f"})

    results = index.search("PM-Kisan subsidy")
    assert len(results) == 2
    assert results[0]["metadata"]["id"] == "doc1"
    assert results[0]["similarity"] > 0.0

def test_memory_manager_ranking():
    manager = MemoryManager()
    now = time.time()

    memories = [
        {"text": "PM-Kisan yojana eligibility", "timestamp": now - 3600, "confidence": 0.95},
        {"text": "Weather rain report Khanna", "timestamp": now, "confidence": 0.8}
    ]

    ranked = manager.rank_memories(memories, "PM-Kisan eligibility")
    # First item should match because of similarity overlap
    assert "PM-Kisan" in ranked[0]["text"]

def test_dialogue_summarization():
    manager = MemoryManager()
    history = [
        ConversationTurn(
            question="What is the price of cotton?",
            intent="Market Price",
            response="Mandi rates show cotton at 7000/quintal.",
            confidence=0.95,
            timestamp=time.time(),
            execution_id="E-1"
        )
    ]
    summary = manager.summarize_conversation(history)
    assert "price of cotton" in summary or "Market Price" in summary
