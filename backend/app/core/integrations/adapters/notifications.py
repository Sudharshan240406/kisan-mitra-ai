import logging

from app.core.integrations.base import INotificationAdapter, IntegrationMetadata

logger = logging.getLogger("kisan_mitra_ai.integrations.adapters.notifications")


class SMSNotificationAdapter(INotificationAdapter):
    """
    SMS Notification Dispatch Adapter.
    """
    def __init__(self) -> None:
        self._metadata = IntegrationMetadata(
            id="sms-notification",
            name="SMS Gateway Service Adapter",
            version="1.0.0",
            description="SMS alert notification dispatch adapter using system channels.",
            type="notifications",
            capabilities=["sms_alerts"],
            configuration={"provider": "mock-sms"},
            feature_flags={"enabled": True}
        )

    @property
    def metadata(self) -> IntegrationMetadata:
        return self._metadata

    async def initialize(self) -> None:
        logger.info("Initializing SMS Notification Adapter...")

    async def cleanup(self) -> None:
        logger.info("Cleaning up SMS Notification resources...")

    async def health_check(self) -> bool:
        return True

    async def send_notification(self, recipient: str, message: str) -> bool:
        logger.info(f"SMS notification sent to recipient {recipient}: {message}")
        return True


class EmailNotificationAdapter(INotificationAdapter):
    """
    Email SMTP Notification Dispatch Adapter.
    """
    def __init__(self) -> None:
        self._metadata = IntegrationMetadata(
            id="email-notification",
            name="Email SMTP Service Adapter",
            version="1.0.0",
            description="Email report and alert notification dispatch SMTP adapter.",
            type="notifications",
            capabilities=["email_reports"],
            configuration={"smtp_server": "smtp.gmail.com"},
            feature_flags={"enabled": False}
        )

    @property
    def metadata(self) -> IntegrationMetadata:
        return self._metadata

    async def initialize(self) -> None:
        logger.info("Initializing Email Notification Adapter...")

    async def cleanup(self) -> None:
        logger.info("Cleaning up Email Notification resources...")

    async def health_check(self) -> bool:
        return True

    async def send_notification(self, recipient: str, message: str) -> bool:
        logger.info(f"Email notification sent to recipient {recipient}: {message}")
        return True


class PushNotificationAdapter(INotificationAdapter):
    """
    Push (FCM/APNS) Notification Dispatch Adapter placeholder.
    """
    def __init__(self) -> None:
        self._metadata = IntegrationMetadata(
            id="push-notification",
            name="FCM Push Notification Adapter",
            version="1.0.0",
            description="FCM and APNS mobile push notification adapter framework.",
            type="notifications",
            capabilities=["push_alerts"],
            configuration={"fcm_key": ""},
            feature_flags={"enabled": False}
        )

    @property
    def metadata(self) -> IntegrationMetadata:
        return self._metadata

    async def initialize(self) -> None:
        logger.info("Initializing Push Notification Adapter...")

    async def cleanup(self) -> None:
        logger.info("Cleaning up Push Notification resources...")

    async def health_check(self) -> bool:
        return True

    async def send_notification(self, recipient: str, message: str) -> bool:
        logger.info(f"Push notification sent to device {recipient}: {message}")
        return True
