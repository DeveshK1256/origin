from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from supabase import Client, create_client

logger = logging.getLogger(__name__)


@dataclass
class AuthState:
    enabled: bool
    required: bool
    provider: str


class SupabaseAuth:
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)

    def get_user(self, token: str) -> dict[str, Any] | None:
        response = self.client.auth.get_user(token)
        user = getattr(response, "user", None)
        if user is None:
            return None
        return {
            "id": getattr(user, "id", None),
            "email": getattr(user, "email", None),
            "role": getattr(user, "role", None),
        }


_AUTH_PROVIDER: SupabaseAuth | None = None
_AUTH_STATE = AuthState(enabled=False, required=False, provider="none")


def _determine_mode() -> str:
    mode = os.getenv("AUTH_MODE", "auto").strip().lower()
    if mode not in {"auto", "required", "optional", "off"}:
        return "auto"
    return mode


def init_auth() -> None:
    global _AUTH_PROVIDER, _AUTH_STATE

    mode = _determine_mode()
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_key = os.getenv("SUPABASE_ANON_KEY", "").strip() or os.getenv(
        "SUPABASE_SERVICE_ROLE_KEY", ""
    ).strip()

    if mode == "off":
        _AUTH_PROVIDER = None
        _AUTH_STATE = AuthState(enabled=False, required=False, provider="none")
        return

    if not (supabase_url and supabase_key):
        required = mode == "required"
        if required:
            logger.warning("AUTH_MODE=required but Supabase auth credentials are missing.")
        _AUTH_PROVIDER = None
        _AUTH_STATE = AuthState(enabled=False, required=required, provider="none")
        return

    try:
        _AUTH_PROVIDER = SupabaseAuth(supabase_url, supabase_key)
        _AUTH_STATE = AuthState(
            enabled=True,
            required=(mode == "required" or mode == "auto"),
            provider="supabase",
        )
    except Exception:
        logger.exception("Failed to initialize Supabase Auth provider.")
        _AUTH_PROVIDER = None
        _AUTH_STATE = AuthState(enabled=False, required=(mode == "required"), provider="none")


def auth_status() -> dict[str, Any]:
    return {
        "enabled": _AUTH_STATE.enabled,
        "required": _AUTH_STATE.required,
        "provider": _AUTH_STATE.provider,
    }


def _extract_bearer_token(headers: Any) -> str | None:
    auth_header = str(headers.get("Authorization") or "").strip()
    if not auth_header:
        return None

    prefix = "bearer "
    if auth_header.lower().startswith(prefix):
        token = auth_header[len(prefix) :].strip()
        return token or None
    return None


def verify_request(headers: Any) -> tuple[dict[str, Any] | None, str | None]:
    token = _extract_bearer_token(headers)

    if not _AUTH_STATE.enabled:
        if _AUTH_STATE.required:
            if not token:
                return None, "Missing bearer token."
            return None, "Auth service is not configured."
        return None, None

    if not token:
        if _AUTH_STATE.required:
            return None, "Missing bearer token."
        return None, None

    try:
        user = _AUTH_PROVIDER.get_user(token) if _AUTH_PROVIDER else None
        if not user:
            return None, "Invalid or expired token."
        return user, None
    except Exception:
        logger.exception("Failed to verify Supabase access token.")
        return None, "Token verification failed."
