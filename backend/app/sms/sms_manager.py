import logging
import time
from typing import Any, Dict, List, Optional

from app.sms.provider_base import SMSStatus
from app.sms.provider_registry import ProviderRegistry
from app.sms.template_engine import TemplateEngine
from app.utils.id import generate_uuid

logger = logging.getLogger("kisan_mitra_ai.sms.sms_manager")


class SMSManager:
    """Orchestrates SMS delivery pipelines, template formatting, retries, and WS telemetry."""

    def __init__(self, registry: ProviderRegistry, template_engine: TemplateEngine, container: Any = None) -> None:
        self.registry = registry
        self.template_engine = template_engine
        self.container = container
        self.fallback_sequence = ["twilio", "msg91", "exotel", "fallback"]

    async def send_sms(
        self,
        recipient: str,
        body: str,
        provider: Optional[str] = None,
        template_key: Optional[str] = None,
        language: Optional[str] = None,
        template_version: str = "v1",
        template_args: Optional[Dict[str, Any]] = None,
    ) -> bool:
        start_time = time.perf_counter()
        sms_id = generate_uuid()

        # 1. Template Rendering
        rendered_body = body
        if template_key:
            rendered_body = self.template_engine.render(
                template_key=template_key,
                language=language or "en",
                version=template_version,
                **(template_args or {})
            )

        # 2. Determine initial provider
        selected_provider_name = provider or ""
        if not selected_provider_name:
            active_p = self.registry.get_active()
            selected_provider_name = active_p.id if active_p else "fallback"

        # 3. Provider Failover Loop
        retry_count = 0
        failure_count = 0
        success = False
        final_provider = selected_provider_name

        queue: List[str] = [selected_provider_name]
        for p in self.fallback_sequence:
            if p not in queue:
                queue.append(p)

        for current_provider_name in queue:
            provider_inst = self.registry.discover(current_provider_name)
            if not provider_inst:
                continue

            final_provider = current_provider_name
            try:
                logger.info(f"[SMSManager] Attempting SMS send via '{current_provider_name}'...")
                res = await provider_inst.send_sms(recipient, rendered_body)
                if res:
                    success = True
                    break
                else:
                    raise ValueError("Send call returned False.")
            except Exception as e:
                logger.warning(
                    f"[SMSManager] Provider '{current_provider_name}' failed to send: {e}. "
                    f"Switching to fallback."
                )
                failure_count += 1
                retry_count += 1

        status = SMSStatus.DELIVERED if success else SMSStatus.FAILED
        latency_ms = (time.perf_counter() - start_time) * 1000

        # 4. Telemetry Observability Logs
        self._record_telemetry(
            provider=final_provider,
            status=status,
            latency_ms=latency_ms,
            retries=retry_count,
            failures=failure_count
        )

        # 5. Broadcast to Mission Control
        self._broadcast_websocket_event(
            direction="outbound",
            sms_id=sms_id,
            recipient=recipient,
            body=rendered_body,
            status=status,
            provider=final_provider,
            latency_ms=latency_ms,
            retries=retry_count
        )

        return success

    def _record_telemetry(
        self,
        provider: str,
        status: SMSStatus,
        latency_ms: float,
        retries: int,
        failures: int
    ) -> None:
        """Publishes operational logging indicators."""
        logger.info(
            f"[SMSTelemetry] provider={provider} status={status.value} "
            f"latency={latency_ms:.1f}ms retries={retries} failures={failures}"
        )
        if self.container and hasattr(self.container, "telemetry") and self.container.telemetry:
            try:
                trace_id = "sms_trace"
                session_id = "sms_session"
                self.container.telemetry.record("sms_latency_ms", latency_ms, trace_id, session_id)
                self.container.telemetry.record("sms_retries", float(retries), trace_id, session_id)
                self.container.telemetry.record("sms_failures", float(failures), trace_id, session_id)
            except Exception as e:
                logger.warning(f"Failed to publish SMS telemetry: {e}")

    def _broadcast_websocket_event(
        self,
        direction: str,
        sms_id: str,
        recipient: str,
        body: str,
        status: SMSStatus,
        provider: str,
        latency_ms: float,
        retries: int
    ) -> None:
        """Pushes events to Mission Control WebSockets."""
        try:
            import asyncio

            from app.api.v1.websocket import ws_manager
            asyncio.create_task(ws_manager.push_event("SMS_TELEMETRY", {
                "direction": direction,
                "sms_id": sms_id,
                "recipient": recipient,
                "body": body,
                "status": status.value,
                "provider": provider,
                "latency_ms": latency_ms,
                "retry_count": retries
            }))
        except Exception as e:
            logger.debug(f"Failed to push SMS WebSocket event: {e}")
