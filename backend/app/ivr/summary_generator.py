import logging
import time
from typing import Any, List, Dict
from app.ivr.call_session import CallSession, CallSummaryModel
from app.personalization.models import LongTermMemory

logger = logging.getLogger("kisan_mitra_ai.ivr.summary_generator")


class SummaryGenerator:
    """Generates a structured call summary and stores it in the personalization Memory Engine."""

    def __init__(self, container: Any) -> None:
        self.container = container

    async def generate_and_store_summary(self, session: CallSession) -> CallSummaryModel:
        """Analyzes the call transcript and saves the summary in the memory engine."""
        transcript_str = "\n".join(
            f"{entry.sender.upper()}: {entry.text}" for entry in session.transcript
        )
        
        # Heuristics for parsing/summarizing
        conversation_summary = "Call discussing agricultural needs."
        weather_advice = ""
        market_advice = ""
        recommended_schemes = []
        action_items = []

        # Attempt to use the LLM Provider for extraction
        llm = getattr(self.container, "llm_provider", None)
        if llm and session.transcript:
            prompt = (
                f"Analyze this farm advisory call transcript and extract key details. "
                f"Format the output strictly as a JSON object with keys: "
                f"'summary' (string), 'schemes' (list of strings), 'weather' (string), "
                f"'market' (string), and 'actions' (list of strings).\n\n"
                f"Transcript:\n{transcript_str}\n\n"
                f"JSON Output:"
            )
            try:
                import inspect
                # Handle synchronous or asynchronous generate method
                if inspect.iscoroutinefunction(llm.generate):
                    response = await llm.generate(prompt)
                else:
                    response = llm.generate(prompt)
                
                if response:
                    # Parse JSON safely
                    import json
                    # Handle model text or clean JSON markers
                    clean_res = response.strip()
                    if "```json" in clean_res:
                        clean_res = clean_res.split("```json")[1].split("```")[0].strip()
                    elif "```" in clean_res:
                        clean_res = clean_res.split("```")[1].split("```")[0].strip()
                    
                    data = json.loads(clean_res)
                    conversation_summary = data.get("summary", conversation_summary)
                    recommended_schemes = data.get("schemes", [])
                    weather_advice = data.get("weather", "")
                    market_advice = data.get("market", "")
                    action_items = data.get("actions", [])
            except Exception as e:
                logger.warning(f"LLM summary generation failed: {e}. Falling back to rule-based summary.")

        # Fallback keyword-based heuristic parsing if LLM failed or wasn't used
        if not weather_advice or not market_advice:
            for entry in session.transcript:
                text_lower = entry.text.lower()
                if "weather" in text_lower or "rain" in text_lower or "temp" in text_lower:
                    weather_advice = "Monitored weather conditions and provided advisories."
                if "price" in text_lower or "market" in text_lower or "rate" in text_lower:
                    market_advice = "Shared latest market price trends."
                if "scheme" in text_lower or "yojana" in text_lower:
                    recommended_schemes.append("Government Scheme eligibility checked.")

        if not action_items:
            action_items = ["Follow recommended agricultural practices as discussed."]

        summary = CallSummaryModel(
            conversation_summary=conversation_summary,
            recommended_schemes=list(set(recommended_schemes)),
            weather_advice=weather_advice,
            market_advice=market_advice,
            action_items=action_items
        )

        session.summary = summary

        # Persist in Personalization Platform Long Term Memory
        farmer_id = session.farmer_id or session.metadata.get("farmer_id") or "guest_farmer"
        try:
            p_platform = self.container.personalization_platform
            memory = p_platform.memories.get(farmer_id)
            if not memory:
                memory = LongTermMemory(farmer_id=farmer_id)
                p_platform.memories[farmer_id] = memory
            
            # Append interaction log
            memory.conversations.append({
                "timestamp": time.time(),
                "query": "[IVR Call Summary]",
                "response": conversation_summary
            })

            # Store summary in memory historical_outcomes
            memory.historical_outcomes.append({
                "type": "ivr_call_summary",
                "call_id": session.call_id,
                "timestamp": time.time(),
                "summary": summary.model_dump()
            })
            p_platform.save_to_disk()
            logger.info(f"Successfully stored call summary in Memory Engine for farmer: {farmer_id}")
        except Exception as e:
            logger.error(f"Failed to store summary in Memory Engine: {e}")

        return summary
