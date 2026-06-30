from __future__ import annotations

import uuid

from apiflask import APIBlueprint, Schema
from flask import request
from marshmallow import fields, validate

from app.api.decorators import require_role
from app.services.admin_service import (
    admin_create_user,
    admin_delete_user,
    admin_update_user,
    create_org,
    delete_org,
    get_org,
    get_user,
    list_orgs,
    list_users,
    update_org,
)

admin_bp = APIBlueprint("admin", __name__, url_prefix="/api/v1/admin")


class OrgCreate(Schema):
    name = fields.String(required=True, validate=validate.Length(max=255))
    slug = fields.String(required=True, validate=validate.Length(max=255))
    settings = fields.Dict(load_default=dict)
    telegram_bot_token = fields.String(allow_none=True, load_default=None)
    telegram_webhook_url = fields.String(allow_none=True, load_default=None)


class OrgUpdate(Schema):
    name = fields.String(validate=validate.Length(max=255))
    slug = fields.String(validate=validate.Length(max=255))
    settings = fields.Dict()
    telegram_bot_token = fields.String(allow_none=True)
    telegram_webhook_url = fields.String(allow_none=True)


class UserCreate(Schema):
    email = fields.String(required=True, validate=validate.Email())
    password = fields.String(required=True, validate=validate.Length(min=8, max=128))
    name = fields.String(required=True, validate=validate.Length(max=255))
    role = fields.String(validate=validate.OneOf(["admin", "operator", "checkin_staff"]), load_default="operator")
    organization_id = fields.String(allow_none=True, load_default=None)


class UserUpdate(Schema):
    email = fields.String(validate=validate.Email())
    password = fields.String(validate=validate.Length(min=8, max=128))
    name = fields.String(validate=validate.Length(max=255))
    role = fields.String(validate=validate.OneOf(["admin", "operator", "checkin_staff"]))
    organization_id = fields.String(allow_none=True)


@admin_bp.get("/orgs")
@require_role("admin")
def admin_list_orgs():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    return list_orgs(page=page, per_page=per_page)


@admin_bp.post("/orgs")
@admin_bp.input(OrgCreate)
@require_role("admin")
def admin_create_org(json_data):
    return create_org(json_data), 201


@admin_bp.get("/orgs/<id>")
@require_role("admin")
def admin_get_org(id: str):
    return get_org(uuid.UUID(id))


@admin_bp.put("/orgs/<id>")
@admin_bp.input(OrgUpdate)
@require_role("admin")
def admin_update_org(id: str, json_data):
    return update_org(uuid.UUID(id), json_data)


@admin_bp.delete("/orgs/<id>")
@require_role("admin")
def admin_delete_org(id: str):
    delete_org(uuid.UUID(id))
    return {}, 204


@admin_bp.get("/users")
@require_role("admin")
def admin_list_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    return list_users(page=page, per_page=per_page)


@admin_bp.post("/users")
@admin_bp.input(UserCreate)
@require_role("admin")
def admin_create_user_route(json_data):
    return admin_create_user(json_data), 201


@admin_bp.get("/users/<id>")
@require_role("admin")
def admin_get_user(id: str):
    return get_user(uuid.UUID(id))


@admin_bp.put("/users/<id>")
@admin_bp.input(UserUpdate)
@require_role("admin")
def admin_update_user_route(id: str, json_data):
    return admin_update_user(uuid.UUID(id), json_data)


@admin_bp.delete("/users/<id>")
@require_role("admin")
def admin_delete_user_route(id: str):
    admin_delete_user(uuid.UUID(id))
    return {}, 204
