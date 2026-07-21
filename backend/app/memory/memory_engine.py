import time
from typing import Any, Dict, List, Optional

from app.memory.conversation_memory import ConversationMemoryStore, ConversationTurn
from app.memory.memory_manager import MemoryManager

# Substores
from app.memory.profile_memory import FarmerProfileMemory, ProfileMemoryStore
from app.memory.recommendation_memory import (
    RecommendationMemoryStore,
)
from app.memory.vector_memory import VectorMemoryIndex


class FarmerMemoryEngine:
    """
    Main memory engine orchestrating profiles, dialogue histories, semantic vector searches,
    relevance ranking, and historical summaries.
    """
    def __init__(self) -> None:
        self.profiles = ProfileMemoryStore()
        self.conversations = ConversationMemoryStore()
        self.recommendations = RecommendationMemoryStore()
        self.vectors = VectorMemoryIndex()
        self.manager = MemoryManager()

    def save_memory(
        self,
        farmer_id: str,
        question: str,
        intent: str,
        response: str,
        confidence: float,
        execution_id: str,
        recommended_schemes: Optional[List[str]] = None,
        applied_schemes: Optional[List[str]] = None,
        rejected_schemes: Optional[List[str]] = None,
        completed_schemes: Optional[List[str]] = None,
        documents_requested: Optional[List[str]] = None,
        documents_submitted: Optional[List[str]] = None
    ) -> None:
        timestamp = time.time()

        # 1. Update Profile (create basic if missing)
        profile = self.profiles.get(farmer_id)
        if not profile:
            profile = FarmerProfileMemory(farmer_id=farmer_id)
            self.profiles.put(profile)

        # 2. Append Conversation Turn
        turn = ConversationTurn(
            question=question,
            intent=intent,
            response=response,
            confidence=confidence,
            timestamp=timestamp,
            execution_id=execution_id
        )
        self.conversations.append(farmer_id, turn)

        # 3. Update Recommendations Record
        rec = self.recommendations.get(farmer_id)
        if recommended_schemes:
            rec.recommended_schemes = list(set(rec.recommended_schemes + recommended_schemes))
        if applied_schemes:
            rec.applied_schemes = list(set(rec.applied_schemes + applied_schemes))
        if rejected_schemes:
            rec.rejected_schemes = list(set(rec.rejected_schemes + rejected_schemes))
        if completed_schemes:
            rec.completed_schemes = list(set(rec.completed_schemes + completed_schemes))
        if documents_requested:
            rec.documents_requested = list(set(rec.documents_requested + documents_requested))
        if documents_submitted:
            rec.documents_submitted = list(set(rec.documents_submitted + documents_submitted))
        self.recommendations.put(farmer_id, rec)

        # 4. Index in Semantic Vector Memory
        self.vectors.add_document(
            text=f"{question} -> {response}",
            metadata={
                "farmer_id": farmer_id,
                "intent": intent,
                "timestamp": timestamp,
                "confidence": confidence
            }
        )

    def retrieve_memory(self, farmer_id: str) -> Dict[str, Any]:
        """
        Gathers profile state, complete conversation records, twin details, and consolidated summaries.
        """
        profile = self.profiles.get(farmer_id) or FarmerProfileMemory(farmer_id=farmer_id)
        history = self.conversations.get_history(farmer_id)
        recommendations = self.recommendations.get(farmer_id)
        summary = self.manager.summarize_conversation(history)

        return {
            "profile": profile.model_dump(),
            "history": [turn.model_dump() for turn in history],
            "recommendations": recommendations.model_dump(),
            "summary": summary,
            "digital_twin": profile.digital_twin_snapshot
        }

    def search_memory(self, farmer_id: str, query: str) -> List[Dict[str, Any]]:
        """
        Searches and ranks vector memories based on relevance and recency.
        """
        # Fetch search list from vector index
        raw_results = self.vectors.search(query, k=10)

        # Filter by farmer_id
        filtered_memories = []
        for doc in raw_results:
            meta = doc["metadata"]
            if meta.get("farmer_id") == farmer_id:
                filtered_memories.append({
                    "text": doc["text"],
                    "timestamp": meta.get("timestamp"),
                    "confidence": meta.get("confidence", 1.0),
                    "intent": meta.get("intent", ""),
                    "similarity": doc["similarity"]
                })

        # Rank via memory manager
        return self.manager.rank_memories(filtered_memories, query)

    def summarize_memory(self, farmer_id: str) -> str:
        history = self.conversations.get_history(farmer_id)
        return self.manager.summarize_conversation(history)

    def delete_memory(self, farmer_id: str) -> None:
        self.conversations.clear(farmer_id)
        self.recommendations.clear(farmer_id)
        # Clear profiles memory entry if required
        if farmer_id in self.profiles.profiles:
            del self.profiles.profiles[farmer_id]
            self.profiles.save()
