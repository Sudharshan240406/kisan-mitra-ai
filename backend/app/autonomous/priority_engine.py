import time


class PriorityEngine:
    """
    Priority evaluation engine scoring events based on urgency and impact factors.
    """
    @staticmethod
    def calculate_priority(due_date: float, urgency_offset: float, impact_score: float) -> str:
        """
        Urgency and impact-based priority classification:
          Score = (0.4 * Urgency) + (0.6 * Impact)

        Outputs: critical | high | medium | low
        """
        time_left = due_date - time.time()

        # Base Urgency from time left
        if time_left <= 86400.0:
            urgency = 10.0
        elif time_left <= 3 * 86400.0:
            urgency = 7.0
        elif time_left <= 7 * 86400.0:
            urgency = 5.0
        else:
            urgency = 2.0

        adjusted_urgency = min(max(urgency + urgency_offset, 0.0), 10.0)

        # Score calculation
        score = (0.4 * adjusted_urgency) + (0.6 * impact_score)

        if score >= 8.0:
            return "critical"
        elif score >= 6.0:
            return "high"
        elif score >= 3.0:
            return "medium"
        else:
            return "low"
