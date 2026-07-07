import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, cast

from app.core.config import settings


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def base64url_decode(data: str) -> bytes:
    padding = "=" * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

class AuthEngine:
    """
    Cryptographic signature and validation engine for JWTs, Refresh Tokens, API Keys, and Service Tokens.
    """
    def __init__(self, secret_key: str = settings.SECRET_KEY) -> None:
        self.secret_key = secret_key

    def generate_jwt(self, payload: Dict[str, Any], exp_seconds: int = 900) -> str:
        """
        Generates an HMAC-SHA256 signed JWT access token.
        """
        header = {"alg": "HS256", "typ": "JWT"}
        claims = payload.copy()
        claims["exp"] = int(time.time()) + exp_seconds
        claims["iat"] = int(time.time())

        header_b64 = base64url_encode(json.dumps(header).encode("utf-8"))
        payload_b64 = base64url_encode(json.dumps(claims).encode("utf-8"))

        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        signature = hmac.new(self.secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
        signature_b64 = base64url_encode(signature)

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def decode_jwt(self, token: str) -> Dict[str, Any]:
        """
        Decodes and verifies an HMAC-SHA256 signed JWT token.
        Raises ValueError if signature or claim validations fail.
        """
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed token structure")

        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_signature = hmac.new(self.secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
        expected_signature_b64 = base64url_encode(expected_signature)

        if not hmac.compare_digest(signature_b64.encode("utf-8"), expected_signature_b64.encode("utf-8")):
            raise ValueError("Token signature verification failed")

        claims = json.loads(base64url_decode(payload_b64).decode("utf-8"))
        if "exp" in claims and claims["exp"] < time.time():
            raise ValueError("Token signature validation: token expired")

        return cast(Dict[str, Any], claims)

    def generate_refresh_token(self, user_id: str, exp_seconds: int = 604800) -> str:
        """
        Generates a refresh token signed using the secret key.
        """
        return self.generate_jwt({"sub": user_id, "type": "refresh"}, exp_seconds=exp_seconds)

    def generate_api_key(self, user_id: str) -> str:
        """
        Generates a secure API key mapping to user ID.
        """
        # km_api_<hash_signature>
        raw_key = f"{user_id}:{time.time()}:api_key"
        signature = hmac.new(self.secret_key.encode("utf-8"), raw_key.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"km_api_{signature[:32]}"

    def generate_service_token(self, service_name: str) -> str:
        """
        Generates a service-to-service integration token.
        """
        # km_svc_<hash_signature>
        raw_key = f"{service_name}:{time.time()}:service_token"
        signature = hmac.new(self.secret_key.encode("utf-8"), raw_key.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"km_svc_{signature[:32]}"
