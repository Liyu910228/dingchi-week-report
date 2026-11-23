"""Signed access-token helpers.

The first local version deliberately keeps the token stateless so the API can
run without a second session store.  Redis remains available for locks and
cache data; token revocation can be added later without changing the API
envelope.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core import signing


class AccessTokenError(ValueError):
    """Raised when a bearer token is absent, expired, or malformed."""


def create_access_token(*, user_id: int, role_code: str) -> str:
    """Create a signed token carrying only the logical user and active role."""
    return signing.dumps(
        {"user_id": str(user_id), "role_code": role_code},
        salt=settings.AUTH_TOKEN_SALT,
        compress=True,
    )


def parse_access_token(token: str) -> dict[str, str]:
    """Validate a bearer token and return its minimal claims."""
    if not token:
        raise AccessTokenError("访问令牌为空。")
    try:
        payload: Any = signing.loads(
            token,
            salt=settings.AUTH_TOKEN_SALT,
            max_age=settings.AUTH_TOKEN_MAX_AGE_SECONDS,
        )
    except (signing.BadSignature, signing.SignatureExpired) as exc:
        raise AccessTokenError("访问令牌无效或已过期。") from exc
    if not isinstance(payload, dict) or not payload.get("user_id") or not payload.get("role_code"):
        raise AccessTokenError("访问令牌缺少必要身份信息。")
    return {"user_id": str(payload["user_id"]), "role_code": str(payload["role_code"])}


def bearer_token_from_header(value: str | None) -> str | None:
    """Extract a bearer token without accepting arbitrary auth schemes."""
    if not value:
        return None
    scheme, separator, token = value.partition(" ")
    if scheme.lower() != "bearer" or not separator or not token.strip():
        return None
    return token.strip()
