import time
from typing import Any, Dict, List

from app.memory.conversation_memory import ConversationTurn


class MemoryManager:
    """
    Ranks relevant memories and manages automatic dialogue history compression.
    """
    def __init__(self) -> None:
        pass

    def rank_memories(self, memories: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Ranks memory nodes by weighted factors: recency (30%), similarity (40%), and confidence (30%).
        """
        now = time.time()
        scored_memories = []

        # Tokenize query for relevance mapping
        query_words = set(query.lower().split())

        for mem in memories:
            timestamp = mem.get("timestamp", now)
            confidence = mem.get("confidence", 1.0)

            # 1. Similarity based on keyword intersection
            text_val = str(mem.get("text", "")).lower()
            text_words = set(text_val.split())
            intersection = query_words.intersection(text_words)
            similarity = len(intersection) / len(query_words.union(text_words)) if query_words else 0.0

            # 2. Recency decay curve
            time_diff = max(0.0, now - timestamp)
            recency = 1.0 / (1.0 + (time_diff / 3600.0)) # hour decay unit

            # Combined score
            score = (0.4 * similarity) + (0.3 * recency) + (0.3 * confidence)

            scored_memories.append((score, mem))

        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_memories]

    def summarize_conversation(self, history: List[ConversationTurn]) -> str:
        """
        Compresses conversation logs to a concise summary of the topics discussed.
        """
        if not history:
            return "No previous conversations recorded."

        topics = []
        for turn in history:
            topics.append(f"Farmer asked: '{turn.question}' -> Agent answered intent: '{turn.intent}'")

        summary = "Consolidated Summary:\n" + "\n".join(topics[-4:])
        return summary
