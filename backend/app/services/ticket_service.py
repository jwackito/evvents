from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.exceptions import ConflictError, NotFoundError
from app.extensions import db
from app.models.attendee import Attendee
from app.models.event import Event
from app.models.ticket import Ticket


def get_ticket_by_qr(qr_hash: str) -> dict:
    ticket = db.session.execute(
        select(Ticket).where(Ticket.qr_hash == qr_hash)
    ).scalar_one_or_none()

    if ticket is None:
        raise NotFoundError("Ticket not found")

    return {"data": _ticket_to_dict(ticket)}


def check_in_ticket(qr_hash: str) -> dict:
    ticket = db.session.execute(
        select(Ticket).where(Ticket.qr_hash == qr_hash)
    ).scalar_one_or_none()

    if ticket is None:
        raise NotFoundError("Ticket not found")

    if ticket.checked_in:
        raise ConflictError("Ticket already checked in")

    ticket.checked_in = True
    ticket.checked_in_at = datetime.now(timezone.utc)
    db.session.commit()

    return {"data": _ticket_to_dict(ticket)}


def link_ticket(qr_hash: str, link_code: str) -> dict:
    ticket = db.session.execute(
        select(Ticket).where(Ticket.qr_hash == qr_hash)
    ).scalar_one_or_none()

    if ticket is None:
        raise NotFoundError("Ticket not found")

    attendee = db.session.get(Attendee, ticket.attendee_id)
    if attendee is None:
        raise NotFoundError("Attendee not found")

    if attendee.link_code != link_code:
        raise ConflictError("Invalid link code")

    attendee.telegram_linked = True
    db.session.commit()

    return {"data": {"message": "Ticket linked successfully"}}


def _ticket_to_dict(ticket: Ticket) -> dict:
    event = db.session.get(Event, ticket.order.event_id)
    attendee = db.session.get(Attendee, ticket.attendee_id)

    return {
        "id": str(ticket.id),
        "qr_hash": ticket.qr_hash,
        "checked_in": ticket.checked_in,
        "checked_in_at": ticket.checked_in_at.isoformat() if ticket.checked_in_at else None,
        "seat": ticket.seat,
        "event": {
            "id": str(event.id) if event else None,
            "title": event.title if event else None,
        },
        "attendee": {
            "id": str(attendee.id) if attendee else None,
            "name": attendee.name if attendee else None,
            "email": attendee.email if attendee else None,
        },
    }
