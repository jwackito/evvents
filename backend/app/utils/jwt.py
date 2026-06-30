from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt as pyjwt
from flask import current_app


def create_access_token(identity: UUID, extra_claims: dict | None = None) -> str:
    expiry = current_app.config["JWT_ACCESS_EXPIRY"]
    payload = {
        "sub": str(identity),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(seconds=expiry),
        "type": "access",
        **(extra_claims or {}),
    }
    return pyjwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def create_refresh_token(identity: UUID) -> str:
    expiry = current_app.config["JWT_REFRESH_EXPIRY"]
    payload = {
        "sub": str(identity),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(seconds=expiry),
        "type": "refresh",
    }
    return pyjwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        return pyjwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
    except pyjwt.PyJWTError:
        return None
