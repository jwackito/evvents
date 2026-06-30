from __future__ import annotations

import uuid
from functools import wraps

from flask import g, request

from app.exceptions import AuthError, ForbiddenError
from app.utils.jwt import decode_token


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise AuthError("Missing or invalid Authorization header")

        token = auth_header.removeprefix("Bearer ")
        payload = decode_token(token)
        if payload is None or payload.get("type") != "access":
            raise AuthError("Invalid or expired token")

        g.user_id = uuid.UUID(payload["sub"])
        return f(*args, **kwargs)

    return decorated


def require_role(*roles: str):
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            from app.services.auth_service import get_user_by_id

            user = get_user_by_id(g.user_id)
            if not user or user.role.value not in roles:
                raise ForbiddenError("Insufficient permissions")
            g.user = user
            return f(*args, **kwargs)

        return decorated

    return decorator
