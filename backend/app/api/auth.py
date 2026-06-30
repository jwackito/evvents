from __future__ import annotations

import uuid

from apiflask import APIBlueprint, Schema
from flask import g, jsonify
from marshmallow import fields, validate

from app.api.decorators import require_auth
from app.exceptions import AuthError
from app.services.auth_service import authenticate, create_user, get_user_by_id
from app.tasks.email_tasks import send_magic_link
from app.utils.jwt import create_access_token, create_refresh_token, decode_token

auth_bp = APIBlueprint("auth", __name__, url_prefix="/api/v1/auth")


class RegisterInput(Schema):
    email = fields.String(required=True, validate=validate.Email())
    password = fields.String(required=True, validate=validate.Length(min=8, max=128))
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))


class LoginInput(Schema):
    email = fields.String(required=True)
    password = fields.String(required=True)


class MagicLinkInput(Schema):
    email = fields.String(required=True, validate=validate.Email())


class MagicLinkVerifyInput(Schema):
    token = fields.String(required=True)


class RefreshInput(Schema):
    refresh_token = fields.String(required=True)


@auth_bp.post("/register")
@auth_bp.input(RegisterInput)
def register(json_data):
    user = create_user(
        email=json_data["email"],
        password=json_data["password"],
        name=json_data["name"],
    )
    access_token = create_access_token(user.id, {"role": user.role.value})
    refresh_token = create_refresh_token(user.id)
    return jsonify({
        "data": {
            "user": {"id": str(user.id), "email": user.email, "name": user.name},
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    }), 201


@auth_bp.post("/login")
@auth_bp.input(LoginInput)
def login(json_data):
    user = authenticate(json_data["email"], json_data["password"])
    if user is None:
        raise AuthError("Invalid email or password")

    access_token = create_access_token(user.id, {"role": user.role.value})
    refresh_token = create_refresh_token(user.id)
    return {
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    }


@auth_bp.post("/magic-link")
@auth_bp.input(MagicLinkInput)
def magic_link(json_data):
    user = get_user_by_email(json_data["email"])
    if user is None:
        return {"data": {"message": "If the email exists, a magic link has been generated"}}

    from flask import current_app

    token = create_access_token(user.id, {"role": user.role.value, "purpose": "magic_link"})
    base_url = current_app.config.get("APP_BASE_URL", "http://localhost:5000")
    send_magic_link(email=json_data["email"], token=token, base_url=base_url)
    return {"data": {"message": "Magic link sent"}}


@auth_bp.get("/magic-link/verify")
@auth_bp.input(MagicLinkVerifyInput, location="query")
def magic_link_verify(query_data):
    payload = decode_token(query_data["token"])
    if payload is None or payload.get("type") != "access" or payload.get("purpose") != "magic_link":
        raise AuthError("Invalid or expired magic link")

    user_id = uuid.UUID(payload["sub"])
    user = get_user_by_id(user_id)
    if user is None:
        raise AuthError("User not found")

    access_token = create_access_token(user.id, {"role": user.role.value})
    refresh_token = create_refresh_token(user.id)
    return {
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    }


@auth_bp.post("/refresh")
@auth_bp.input(RefreshInput)
def refresh(json_data):
    payload = decode_token(json_data["refresh_token"])
    if payload is None or payload.get("type") != "refresh":
        raise AuthError("Invalid or expired refresh token")

    user_id = uuid.UUID(payload["sub"])
    user = get_user_by_id(user_id)
    if user is None:
        raise AuthError("User not found")

    access_token = create_access_token(user.id, {"role": user.role.value})
    refresh_token = create_refresh_token(user.id)
    return {
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    }


@auth_bp.get("/me")
@require_auth
def me():
    user = get_user_by_id(g.user_id)
    return {
        "data": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
        }
    }


def get_user_by_email(email: str):
    from sqlalchemy import select

    from app.extensions import db
    from app.models.user import User

    return db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
