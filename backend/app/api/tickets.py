from __future__ import annotations

from apiflask import APIBlueprint, Schema
from flask import request
from marshmallow import fields, validate

from app.api.decorators import require_auth, require_role
from app.services.order_service import create_order, get_order, get_user_orders
from app.services.ticket_service import check_in_ticket, get_ticket_by_qr, link_ticket
from app.services.waitlist_service import get_position, join_waitlist, leave_waitlist

tickets_bp = APIBlueprint("tickets", __name__, url_prefix="/api/v1")


class OrderInput(Schema):
    ticket_type_id = fields.String(required=True)
    quantity = fields.Integer(required=True, validate=validate.Range(min=1, max=10))
    attendee_name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    attendee_email = fields.Email(allow_none=True, load_default=None)
    telegram_chat_id = fields.Integer(allow_none=True, load_default=None)


class CheckInInput(Schema):
    qr_hash = fields.String(required=True)


class LinkInput(Schema):
    qr_hash = fields.String(required=True)
    link_code = fields.String(required=True)


@tickets_bp.post("/events/<slug>/order")
@tickets_bp.input(OrderInput)
def order_tickets(slug: str, json_data):
    return create_order(
        event_slug=slug,
        ticket_type_id=json_data["ticket_type_id"],
        quantity=json_data["quantity"],
        attendee_name=json_data["attendee_name"],
        attendee_email=json_data.get("attendee_email"),
        telegram_chat_id=json_data.get("telegram_chat_id"),
    ), 201


@tickets_bp.get("/tickets/<code>")
def ticket_detail(code: str):
    return get_ticket_by_qr(code)


@tickets_bp.post("/tickets/check-in")
@tickets_bp.input(CheckInInput)
@require_auth
def check_in(json_data):
    return check_in_ticket(json_data["qr_hash"])


@tickets_bp.post("/tickets/link")
@tickets_bp.input(LinkInput)
def link(json_data):
    return link_ticket(json_data["qr_hash"], json_data["link_code"])


@tickets_bp.get("/orders/<id>")
def order_detail(id: str):
    return get_order(id)


@tickets_bp.get("/me/orders")
@require_auth
def my_orders():
    from flask import g

    return get_user_orders(g.user.email)


class WaitlistJoinInput(Schema):
    ticket_type_id = fields.String(required=True)
    attendee_name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    attendee_email = fields.Email(allow_none=True, load_default=None)


class WaitlistLeaveInput(Schema):
    link_code = fields.String(required=True)


@tickets_bp.post("/events/<slug>/waitlist")
@tickets_bp.input(WaitlistJoinInput)
def waitlist_join(slug: str, json_data):
    return join_waitlist(
        event_slug=slug,
        ticket_type_id=json_data["ticket_type_id"],
        attendee_name=json_data["attendee_name"],
        attendee_email=json_data.get("attendee_email"),
    ), 201


@tickets_bp.delete("/waitlist/<id>")
@tickets_bp.input(WaitlistLeaveInput, location="json")
def waitlist_leave(id: str, json_data):
    leave_waitlist(id, json_data["link_code"])
    return {}, 204


@tickets_bp.get("/events/<slug>/waitlist/position")
def waitlist_position(slug: str):
    email = request.args.get("email", "")
    return get_position(slug, email)
