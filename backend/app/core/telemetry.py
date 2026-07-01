import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field


class TelemetryEntry(BaseModel):
    """
    Standard envelope capturing a telemetry measurement point.
    """
    metric_name: str
    value: Any
    trace_id: str
    session_id: str
    timestamp: float = Field(default_factory=time.time)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ITelemetryExporter(ABC):
    """
    Interface definition for platform telemetry exporters.
    """
    @abstractmethod
    def record(
        self,
        name: str,
        value: Any,
        trace_id: str,
        session_id: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Records a single metric measurement.
        """
        pass

    @abstractmethod
    def export_metrics(self) -> dict[str, Any]:
        """
        Compiles and retrieves aggregate metric summaries.
        """
        pass


class TelemetryFramework(ITelemetryExporter):
    """
    Centralized structured telemetry framework recording execution statistics.
    """
    def __init__(self) -> None:
        self._entries: list[TelemetryEntry] = []

    def record(
        self,
        name: str,
        value: Any,
        trace_id: str,
        session_id: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        entry = TelemetryEntry(
            metric_name=name,
            value=value,
            trace_id=trace_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        self._entries.append(entry)

    def export_metrics(self) -> dict[str, Any]:
        # Track counts/latencies dynamically
        planning_latencies = [e.value for e in self._entries if e.metric_name == "planning_latency_ms"]
        workflow_latencies = [e.value for e in self._entries if e.metric_name == "workflow_latency_ms"]
        decision_latencies = [e.value for e in self._entries if e.metric_name == "decision_latency_ms"]
        agent_latencies: dict[str, list[float]] = {}
        for e in self._entries:
            if e.metric_name == "agent_execution_time_ms":
                agent_name = e.metadata.get("agent_name", "Unknown")
                agent_latencies[agent_name] = [*agent_latencies.get(agent_name, []), e.value]

        evidence_counts = [e.value for e in self._entries if e.metric_name == "evidence_count"]
        reasoning_depths = [e.value for e in self._entries if e.metric_name == "reasoning_depth"]
        graph_sizes = [e.value for e in self._entries if e.metric_name == "reasoning_graph_size"]
        confidences = [e.value for e in self._entries if e.metric_name == "confidence"]
        safety_interventions = len([e for e in self._entries if e.metric_name == "safety_intervention"])
        policy_violations = len([e for e in self._entries if e.metric_name == "policy_violation"])
        memory_usages = [e.value for e in self._entries if e.metric_name == "memory_usage_bytes"]

        # Omnichannel metrics
        channel_routing_latencies = [e.value for e in self._entries if e.metric_name == "channel_routing_latency_ms"]
        channel_response_times = [e.value for e in self._entries if e.metric_name == "channel_response_time_ms"]
        session_durations = [e.value for e in self._entries if e.metric_name == "channel_session_duration_seconds"]
        channel_delivery_errors = len([e for e in self._entries if e.metric_name == "channel_delivery_error"])

        channel_utilization: dict[str, int] = {}
        for e in self._entries:
            if e.metric_name == "channel_message_processed":
                ch_id = e.metadata.get("channel_id", "unknown")
                channel_utilization[ch_id] = channel_utilization.get(ch_id, 0) + 1

        total_channel_messages = len(channel_routing_latencies)
        channel_error_rate = channel_delivery_errors / total_channel_messages if total_channel_messages > 0 else 0.0

        # Media metrics
        media_processing_latencies = [e.value for e in self._entries if e.metric_name == "media_processing_latency_ms"]
        media_validation_failures = len([e for e in self._entries if e.metric_name == "media_validation_failure"])
        media_policy_violations = len([e for e in self._entries if e.metric_name == "media_policy_violation"])

        media_utilization: dict[str, int] = {}
        for e in self._entries:
            if e.metric_name == "media_processing_latency_ms":
                m_type = e.metadata.get("media_type", "unknown")
                media_utilization[m_type] = media_utilization.get(m_type, 0) + 1

        total_media_processed = len(media_processing_latencies)

        voice_session_count = sum(int(e.value) for e in self._entries if e.metric_name == "voice_session_count")
        speech_latencies = [e.value for e in self._entries if e.metric_name == "speech_processing_latency_ms"]
        speech_confidences = [e.value for e in self._entries if e.metric_name == "speech_confidence"]

        vision_upload_count = sum(int(e.value) for e in self._entries if e.metric_name == "vision_upload_count")
        vision_latencies = [e.value for e in self._entries if e.metric_name == "vision_processing_latency_ms"]
        vision_confidences = [e.value for e in self._entries if e.metric_name == "vision_confidence"]

        ocr_request_count = sum(int(e.value) for e in self._entries if e.metric_name == "ocr_request_count")
        ocr_latencies = [e.value for e in self._entries if e.metric_name == "ocr_processing_latency_ms"]
        ocr_confidences = [e.value for e in self._entries if e.metric_name == "ocr_confidence"]

        multimodal_latencies = [e.value for e in self._entries if e.metric_name == "multimodal_processing_latency_ms"]
        multimodal_confidences = [e.value for e in self._entries if e.metric_name == "multimodal_confidence"]
        multimodal_reasoning = [e.value for e in self._entries if e.metric_name == "multimodal_reasoning_integration"]

        # Telephony metrics
        telephony_durations = [e.value for e in self._entries if e.metric_name == "telephony_call_duration_seconds"]
        telephony_ivr_completions = [e.value for e in self._entries if e.metric_name == "telephony_ivr_completion"]
        telephony_latencies = [e.value for e in self._entries if e.metric_name == "telephony_routing_latency_ms"]
        telephony_retries = [e.value for e in self._entries if e.metric_name == "telephony_retry_count"]
        telephony_errors = len([e for e in self._entries if e.metric_name == "telephony_error_count"])

        total_calls = len(telephony_durations)
        avg_call_duration = sum(telephony_durations) / total_calls if total_calls > 0 else 0.0
        ivr_completion_rate = sum(telephony_ivr_completions) / len(telephony_ivr_completions) if telephony_ivr_completions else 0.0
        avg_telephony_latency = sum(telephony_latencies) / len(telephony_latencies) if telephony_latencies else 0.0
        total_retries = sum(telephony_retries) if telephony_retries else 0
        telephony_error_rate = telephony_errors / total_calls if total_calls > 0 else 0.0

        # SMS metrics
        sms_received_total = len([e for e in self._entries if e.metric_name == "sms_received_count"])
        sms_sent_total = len([e for e in self._entries if e.metric_name == "sms_sent_count"])
        sms_failures = len([e for e in self._entries if e.metric_name == "sms_delivery_failure"])
        sms_validation_failures = len([e for e in self._entries if e.metric_name == "sms_validation_failure"])
        sms_policy_violations = len([e for e in self._entries if e.metric_name == "sms_policy_violation"])
        sms_retries_total = sum([e.value for e in self._entries if e.metric_name == "sms_retry_count"])
        sms_latencies = [e.value for e in self._entries if e.metric_name == "sms_processing_latency_ms"]

        sms_delivery_rate = (sms_sent_total - sms_failures) / sms_sent_total if sms_sent_total > 0 else 0.0
        avg_sms_latency = sum(sms_latencies) / len(sms_latencies) if sms_latencies else 0.0

        sms_languages: dict[str, int] = {}
        for e in self._entries:
            if e.metric_name == "sms_session_language":
                lang = e.metadata.get("language", "unknown")
                sms_languages[lang] = sms_languages.get(lang, 0) + 1

        sms_continuity_vals = [e.value for e in self._entries if e.metric_name == "sms_session_continuity"]
        avg_continuity = sum(sms_continuity_vals) / len(sms_continuity_vals) if sms_continuity_vals else 0.0

        # Integration metrics calculations
        integration_latencies = [e.value for e in self._entries if e.metric_name == "integration_latency_ms"]
        integration_failures = len([e for e in self._entries if e.metric_name == "integration_failure"])
        integration_costs = [e.value for e in self._entries if e.metric_name == "integration_cost_usd"]
        total_integration_cost = sum(integration_costs) if integration_costs else 0.0

        integration_retry_count = 0
        integration_breakdown = {}
        for e in self._entries:
            if e.metric_name == "integration_latency_ms":
                i_id = e.metadata.get("integration_id", "unknown")
                attempts = e.metadata.get("attempts", 0)
                integration_retry_count += attempts
                status = e.metadata.get("status", "success")

                if i_id not in integration_breakdown:
                    integration_breakdown[i_id] = {"latencies": [], "failures": 0, "retries": 0}
                integration_breakdown[i_id]["latencies"].append(e.value)
                integration_breakdown[i_id]["retries"] += attempts
                if status == "failed":
                    integration_breakdown[i_id]["failures"] += 1

        integration_summary = {
            name: {
                "avg_latency_ms": sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0.0,
                "failures": stats["failures"],
                "retries": stats["retries"],
                "total_calls": len(stats["latencies"])
            }
            for name, stats in integration_breakdown.items()
        }

        return {
            "planning_latency": {
                "avg_ms": sum(planning_latencies) / len(planning_latencies) if planning_latencies else 0.0,
                "count": len(planning_latencies)
            },
            "workflow_latency": {
                "avg_ms": sum(workflow_latencies) / len(workflow_latencies) if workflow_latencies else 0.0,
                "count": len(workflow_latencies)
            },
            "decision_latency": {
                "avg_ms": sum(decision_latencies) / len(decision_latencies) if decision_latencies else 0.0,
                "count": len(decision_latencies)
            },
            "agent_execution_times": {
                name: sum(times) / len(times) for name, times in agent_latencies.items()
            },
            "evidence_count_total": sum(evidence_counts) if evidence_counts else 0,
            "max_reasoning_depth": max(reasoning_depths) if reasoning_depths else 0,
            "max_graph_size": max(graph_sizes) if graph_sizes else 0,
            "confidence_distribution": confidences,
            "safety_interventions_count": safety_interventions,
            "policy_violations_count": policy_violations,
            "max_memory_usage_bytes": max(memory_usages) if memory_usages else 0,
            "channel_metrics": {
                "messages_processed": total_channel_messages,
                "avg_routing_latency_ms": sum(channel_routing_latencies) / len(channel_routing_latencies) if channel_routing_latencies else 0.0,
                "avg_response_time_ms": sum(channel_response_times) / len(channel_response_times) if channel_response_times else 0.0,
                "avg_session_duration_seconds": sum(session_durations) / len(session_durations) if session_durations else 0.0,
                "channel_utilization": channel_utilization,
                "error_rate": channel_error_rate,
                "error_count": channel_delivery_errors
            },
            "media_metrics": {
                "total_processed": total_media_processed,
                "avg_processing_latency_ms": sum(media_processing_latencies) / len(media_processing_latencies) if media_processing_latencies else 0.0,
                "validation_failures": media_validation_failures,
                "policy_violations": media_policy_violations,
                "media_utilization": media_utilization
            },
            "voice_metrics": {
                "total_sessions": voice_session_count,
                "avg_processing_latency_ms": sum(speech_latencies) / len(speech_latencies) if speech_latencies else 0.0,
                "avg_confidence": sum(speech_confidences) / len(speech_confidences) if speech_confidences else 0.0,
            },
            "vision_metrics": {
                "total_uploads": vision_upload_count,
                "avg_processing_latency_ms": sum(vision_latencies) / len(vision_latencies) if vision_latencies else 0.0,
                "avg_confidence": sum(vision_confidences) / len(vision_confidences) if vision_confidences else 0.0,
            },
            "ocr_metrics": {
                "total_requests": ocr_request_count,
                "avg_processing_latency_ms": sum(ocr_latencies) / len(ocr_latencies) if ocr_latencies else 0.0,
                "avg_confidence": sum(ocr_confidences) / len(ocr_confidences) if ocr_confidences else 0.0,
            },
            "multimodal_metrics": {
                "total_processed": len(multimodal_latencies),
                "avg_processing_latency_ms": sum(multimodal_latencies) / len(multimodal_latencies) if multimodal_latencies else 0.0,
                "avg_confidence": sum(multimodal_confidences) / len(multimodal_confidences) if multimodal_confidences else 0.0,
                "reasoning_integration_rate": sum(multimodal_reasoning) / len(multimodal_reasoning) if multimodal_reasoning else 0.0,
            },
            "telephony_metrics": {
                "total_calls": total_calls,
                "avg_call_duration_seconds": avg_call_duration,
                "ivr_completion_rate": ivr_completion_rate,
                "avg_routing_latency_ms": avg_telephony_latency,
                "total_retries": total_retries,
                "error_rate": telephony_error_rate,
                "error_count": telephony_errors
            },
            "sms_metrics": {
                "received_count": sms_received_total,
                "sent_count": sms_sent_total,
                "delivery_rate": sms_delivery_rate,
                "retry_count": sms_retries_total,
                "avg_processing_latency_ms": avg_sms_latency,
                "validation_failures": sms_validation_failures,
                "policy_violations": sms_policy_violations,
                "avg_continuity": avg_continuity,
                "language_distribution": sms_languages
            },
            "integration_metrics": {
                "total_calls": len(integration_latencies),
                "avg_latency_ms": sum(integration_latencies) / len(integration_latencies) if integration_latencies else 0.0,
                "failure_count": integration_failures,
                "retry_count": integration_retry_count,
                "total_cost_usd": total_integration_cost,
                "adapters": integration_summary
            },
            "ai_metrics": self._aggregate_ai_metrics(),
            "system_stats": self.get_system_stats()
        }

    def _aggregate_ai_metrics(self) -> dict[str, Any]:
        """
        Compiles and aggregates telemetry metrics for all AI platform model invocations.
        """
        ai_token_entries = [e for e in self._entries if e.metric_name == "ai_tokens_count"]
        ai_cost_entries = [e for e in self._entries if e.metric_name == "ai_execution_cost_usd"]
        ai_latency_entries = [e for e in self._entries if e.metric_name == "ai_execution_latency_ms"]

        fallback_count = len([
            e for e in ai_token_entries
            if e.metadata.get("is_fallback", False)
        ])

        total_tokens = sum([int(e.value) for e in ai_token_entries])
        total_cost = sum([float(e.value) for e in ai_cost_entries])

        model_latencies: dict[str, list[float]] = {}
        for e in ai_latency_entries:
            m_id = e.metadata.get("model_id", "unknown")
            if m_id not in model_latencies:
                model_latencies[m_id] = []
            model_latencies[m_id].append(float(e.value))

        model_summary = {
            m_id: round(sum(lats) / len(lats), 2)
            for m_id, lats in model_latencies.items()
            if lats
        }

        return {
            "total_requests": len(ai_token_entries),
            "total_tokens_consumed": total_tokens,
            "total_estimated_cost_usd": round(total_cost, 6),
            "fallback_executions": fallback_count,
            "average_latency_by_model_ms": model_summary
        }


    def get_system_stats(self) -> dict[str, Any]:
        """
        Retrieves container CPU and Memory metrics dynamically, failing back safely.
        """
        import os
        import sys

        stats = {
            "cpu_percent": 0.0,
            "memory_usage_mb": 0.0,
            "pid": os.getpid()
        }

        # 1. Fetch memory usage via resource module (Unix/Linux friendly)
        try:
            import resource
            max_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if sys.platform == "darwin":  # macOS ru_maxrss is in bytes
                stats["memory_usage_mb"] = round(max_rss / (1024 * 1024), 2)
            else:  # Linux ru_maxrss is in kilobytes
                stats["memory_usage_mb"] = round(max_rss / 1024, 2)
        except Exception:
            pass

        # 2. Try psutil for higher precision measurements if installed
        try:
            import psutil
            proc = psutil.Process(os.getpid())
            stats["cpu_percent"] = round(proc.cpu_percent(interval=None), 2)
            stats["memory_usage_mb"] = round(proc.memory_info().rss / (1024 * 1024), 2)
        except ImportError:
            # Fallback user + system CPU times metric
            try:
                times = os.times()
                stats["cpu_percent"] = round((times.user + times.system), 2)
            except Exception:
                pass

        return stats
