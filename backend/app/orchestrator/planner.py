from typing import List


class DynamicPlanner:
    """
    Decides which agents/services are required to satisfy the detected intent.
    """
    def __init__(self) -> None:
        # Map intents to required agent identifiers
        self.intent_map = {
            "Government Scheme": ["GovernmentScheme", "Knowledge", "LLM"],
            "Weather": ["Weather", "Knowledge", "LLM"],
            "Market Price": ["Market", "Knowledge", "LLM"],
            "Crop Disease": ["Knowledge", "LLM"],
            "Document Help": ["GovernmentScheme", "Memory", "LLM"],
            "Greeting": ["Memory", "LLM"],
            "Voice Command": ["Memory", "LLM"],
            "General Question": ["Memory", "Knowledge", "LLM"]
        }

    def select_agents(self, intent: str) -> List[str]:
        return self.intent_map.get(intent, ["Memory", "Knowledge", "LLM"])
