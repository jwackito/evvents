from __future__ import annotations

import uuid

from apiflask import APIBlueprint, Schema
from flask import g, request
from marshmallow import fields, validate

from app.api.decorators import require_role
from app.exceptions import ForbiddenError
from app.services.org_service import (
    create_event,
    create_ticket_type,
    delete_event,
    delete_ticket_type,
    get_event_orders,
    get_event_stats,
    get_org_event_by_slug,
    list_checkin_events,
    list_org_events,
    list_ticket_types,
    update_bot_config,
    update_event,
    update_ticket_type,
)
from app.services.seating_service import assign_seat, bulk_assign, get_seating, release_seat
from app.services.waitlist_service import claim_entry, list_event_waitlist

org_bp = APIBlueprint("org", __name__, url_prefix="/api/v1/org")


def _require_org() -> uuid.UUID:
    org_id = g.user.organization_id
    if org_id is None:
        raise ForbiddenError("User does not belong to an organization")
    return org_id


class EventCreate(Schema):
    title = fields.String(required=True, validate=validate.Length(max=255))
    description = fields.String(allow_none=True, load_default=None)
    date = fields.DateTime(required=True)
    location = fields.String(allow_none=True, validate=validate.Length(max=255), load_default=None)
    capacity = fields.Integer(required=True, validate=validate.Range(min=1))
    status = fields.String(validate=validate.OneOf(["draft", "published", "cancelled", "completed"]), load_default="draft")
    seating_type = fields.String(validate=validate.OneOf(["general", "assigned"]), load_default="general")
    slug = fields.String(required=True, validate=validate.Length(max=255))
    cover_image = fields.String(allow_none=True, load_default=None)


class EventUpdate(Schema):
    title = fields.String(validate=validate.Length(max=255))
    description = fields.String(allow_none=True)
    date = fields.DateTime()
    location = fields.String(allow_none=True, validate=validate.Length(max=255))
    capacity = fields.Integer(validate=validate.Range(min=1))
    slug = fields.String(validate=validate.Length(max=255))
    status = fields.String(validate=validate.OneOf(["draft", "published", "cancelled", "completed"]))
    seating_type = fields.String(validate=validate.OneOf(["general", "assigned"]))
    cover_image = fields.String(allow_none=True)


class TicketTypeCreate(Schema):
    name = fields.String(required=True, validate=validate.Length(max=255))
    description = fields.String(allow_none=True, load_default=None)
    price = fields.Integer(load_default=0, validate=validate.Range(min=0))
    capacity = fields.Integer(required=True, validate=validate.Range(min=1))
    max_per_order = fields.Integer(load_default=5, validate=validate.Range(min=1))


class TicketTypeUpdate(Schema):
    name = fields.String(validate=validate.Length(max=255))
    description = fields.String(allow_none=True)
    price = fields.Integer(validate=validate.Range(min=0))
    capacity = fields.Integer(validate=validate.Range(min=1))
    max_per_order = fields.Integer(validate=validate.Range(min=1))


class BotConfigUpdate(Schema):
    telegram_bot_token = fields.String(allow_none=True)
    telegram_webhook_url = fields.String(allow_none=True)


@org_bp.get("/events")
@require_role("admin", "operator", "checkin_staff")
def org_list_events():
    org_id = _require_org()
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    return list_org_events(org_id, status=status, page=page, per_page=per_page)


@org_bp.get("/events/<slug>")
@require_role("admin", "operator", "checkin_staff")
def org_get_event(slug: str):
    org_id = _require_org()
    return get_org_event_by_slug(slug, org_id)


@org_bp.post("/events")
@org_bp.input(EventCreate)
@require_role("admin", "operator")
def org_create_event(json_data):
    org_id = _require_org()
    return create_event(org_id, json_data), 201


@org_bp.put("/events/<id>")
@org_bp.input(EventUpdate)
@require_role("admin", "operator")
def org_update_event(id: str, json_data):
    org_id = _require_org()
    return update_event(uuid.UUID(id), org_id, json_data)


@org_bp.delete("/events/<id>")
@require_role("admin")
def org_delete_event(id: str):
    org_id = _require_org()
    delete_event(uuid.UUID(id), org_id)
    return {}, 204


@org_bp.get("/events/<id>/ticket-types")
@require_role("admin", "operator", "checkin_staff")
def org_list_ticket_types(id: str):
    org_id = _require_org()
    return list_ticket_types(uuid.UUID(id), org_id)


@org_bp.post("/events/<id>/ticket-types")
@org_bp.input(TicketTypeCreate)
@require_role("admin", "operator")
def org_create_ticket_type(id: str, json_data):
    org_id = _require_org()
    return create_ticket_type(uuid.UUID(id), org_id, json_data)


@org_bp.put("/events/<event_id>/ticket-types/<tt_id>")
@org_bp.input(TicketTypeUpdate)
@require_role("admin", "operator")
def org_update_ticket_type(event_id: str, tt_id: str, json_data):
    org_id = _require_org()
    return update_ticket_type(uuid.UUID(event_id), uuid.UUID(tt_id), org_id, json_data)


@org_bp.delete("/events/<event_id>/ticket-types/<tt_id>")
@require_role("admin")
def org_delete_ticket_type(event_id: str, tt_id: str):
    org_id = _require_org()
    delete_ticket_type(uuid.UUID(event_id), uuid.UUID(tt_id), org_id)
    return {}, 204


@org_bp.get("/events/<id>/orders")
@require_role("admin", "operator")
def org_event_orders(id: str):
    org_id = _require_org()
    return get_event_orders(uuid.UUID(id), org_id)


@org_bp.get("/events/<id>/stats")
@require_role("admin", "operator", "checkin_staff")
def org_event_stats(id: str):
    org_id = _require_org()
    return get_event_stats(uuid.UUID(id), org_id)


@org_bp.put("/bot-config")
@org_bp.input(BotConfigUpdate)
@require_role("admin")
def org_bot_config(json_data):
    org_id = _require_org()
    return update_bot_config(org_id, json_data)


@org_bp.get("/check-in")
@require_role("admin", "operator", "checkin_staff")
def org_checkin():
    org_id = _require_org()
    return list_checkin_events(org_id)


@org_bp.get("/events/<id>/waitlist")
@require_role("admin", "operator")
def org_waitlist(id: str):
    org_id = _require_org()
    return list_event_waitlist(uuid.UUID(id), org_id)


@org_bp.post("/events/<event_id>/waitlist/<entry_id>/claim")
@require_role("admin")
def org_claim_waitlist(event_id: str, entry_id: str):
    org_id = _require_org()
    return claim_entry(uuid.UUID(entry_id), org_id, uuid.UUID(event_id))


@org_bp.get("/events/<id>/seating")
@require_role("admin", "operator", "checkin_staff")
def org_get_seating(id: str):
    org_id = _require_org()
    return get_seating(uuid.UUID(id), org_id)


class SeatAssign(Schema):
    seat = fields.String(required=True, validate=validate.Length(max=50))


class SeatBulkAssign(Schema):
    assignments = fields.Dict(
        keys=fields.String(),
        values=fields.String(allow_none=True),
        required=True,
    )


@org_bp.put("/events/<event_id>/seating/<ticket_id>")
@org_bp.input(SeatAssign)
@require_role("admin", "operator")
def org_assign_seat(event_id: str, ticket_id: str, json_data):
    org_id = _require_org()
    return assign_seat(uuid.UUID(event_id), uuid.UUID(ticket_id), org_id, json_data["seat"])


@org_bp.delete("/events/<event_id>/seating/<ticket_id>")
@require_role("admin", "operator")
def org_release_seat(event_id: str, ticket_id: str):
    org_id = _require_org()
    release_seat(uuid.UUID(event_id), uuid.UUID(ticket_id), org_id)
    return {}, 204


@org_bp.put("/events/<id>/seating/bulk")
@org_bp.input(SeatBulkAssign)
@require_role("admin", "operator")
def org_bulk_assign_seats(id: str, json_data):
    org_id = _require_org()
    return bulk_assign(uuid.UUID(id), org_id, json_data["assignments"])
