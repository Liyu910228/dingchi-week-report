"""Attach validated bearer claims to every Django request."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from apps.core.authentication.token import bearer_token_from_header, parse_access_token


class AuthContextMiddleware:
    """Decode the access token once; business services resolve logical users."""

    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> Any:
        request.auth_claims = None  # type: ignore[attr-defined]
        token = bearer_token_from_header(request.headers.get("Authorization"))
        if token:
            try:
                request.auth_claims = parse_access_token(token)  # type: ignore[attr-defined]
            except Exception:
                # Invalid credentials are handled by the endpoint's uniform
                # authentication guard; the middleware never leaks token details.
                request.auth_claims = None  # type: ignore[attr-defined]
        return self.get_response(request)
