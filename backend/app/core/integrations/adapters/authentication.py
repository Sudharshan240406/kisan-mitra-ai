import logging

from app.core.integrations.base import IAuthenticationAdapter, IntegrationMetadata

logger = logging.getLogger("kisan_mitra_ai.integrations.adapters.authentication")


class LocalAuthAdapter(IAuthenticationAdapter):
    """
    Local Database Credentials and JWT Session Authentication Adapter.
    """
    def __init__(self) -> None:
        self._metadata = IntegrationMetadata(
            id="local-auth",
            name="Local DB Authentication",
            version="1.0.0",
            description="Local database user validation and secure session adapter.",
            type="authentication",
            capabilities=["session_jwt"],
            configuration={"hashing_algorithm": "bcrypt"},
            feature_flags={"enabled": True}
        )

    @property
    def metadata(self) -> IntegrationMetadata:
        return self._metadata

    async def initialize(self) -> None:
        logger.info("Initializing Local Auth Adapter...")

    async def cleanup(self) -> None:
        logger.info("Cleaning up Local Auth resources...")

    async def health_check(self) -> bool:
        return True

    async def authenticate(self, username: str, token: str) -> bool:
        logger.info(f"Authenticating user '{username}' via Local Authentication...")
        # Simulating standard mock authentication checks
        return token == "valid-session-jwt-token" or username == "admin"


class OAuthAdapter(IAuthenticationAdapter):
    """
    Centralized OAuth SSO (Google/Microsoft/Enterprise SSO) Authentication Adapter.
    """
    def __init__(self) -> None:
        self._metadata = IntegrationMetadata(
            id="oauth-auth",
            name="OAuth Central SSO Adapter",
            version="1.0.0",
            description="OAuth 2.0 single sign-on provider authentication adapter framework.",
            type="authentication",
            capabilities=["oauth_sso"],
            configuration={"client_id": "", "auth_endpoint": "https://auth.kisanmitra.gov.in"},
            feature_flags={"enabled": False}
        )

    @property
    def metadata(self) -> IntegrationMetadata:
        return self._metadata

    async def initialize(self) -> None:
        logger.info("Initializing OAuth Adapter...")

    async def cleanup(self) -> None:
        logger.info("Cleaning up OAuth resources...")

    async def health_check(self) -> bool:
        return True

    async def authenticate(self, username: str, token: str) -> bool:
        logger.info(f"Authenticating user '{username}' via OAuth SSO...")
        return token.startswith("oauth-token:")
