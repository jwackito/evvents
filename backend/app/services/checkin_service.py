from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select

from app.exceptions import ConflictError, NotFoundError, ForbiddenError
from app.extensions import db
from app.models.attendee import Attendee
from app.models.event import Event, EventStatus
from app.models.order import Order, OrderStatus
from app.models.ticket import Ticket
from app.models.ticket_type import TicketType


def get_checkin_events(org_id: uuid.UUID) -> dict:
    events = db.session.execute(
        select(Event)
        .where(
            Event.organization_id == org_id,
            Event.status.in_([EventStatus.PUBLISHED, EventStatus.COMPLETED]),
        )
        .order_by(Event.date.desc())
    ).scalars().all()

    return {
        "data": [
            {
                "id": str(e.id),
                "title": e.title,
                "date": e.date.isoformat(),
                "slug": e.slug,
            }
            for e in events
        ]
    }


def scan_ticket(org_id: uuid.UUID, qr_hash: str) -> dict:
    ticket = db.session.execute(
        select(Ticket).where(Ticket.qr_hash == qr_hash)
    ).scalar_one_or_none()

    if ticket is None:
        raise NotFoundError("Ticket not found")

    event = db.session.get(Event, ticket.order.event_id)
    if event is None or event.organization_id != org_id:
        raise ForbiddenError("Ticket does not belong to this organization")

    if ticket.checked_in:
        raise ConflictError("Ticket already checked in")

    ticket.checked_in = True
    ticket.checked_in_at = datetime.now(timezone.utc)
    db.session.commit()

    return {"data": _ticket_to_dict(ticket)}


def undo_check_in(org_id: uuid.UUID, qr_hash: str) -> dict:
    ticket = db.session.execute(
        select(Ticket).where(Ticket.qr_hash == qr_hash)
    ).scalar_one_or_none()

    if ticket is None:
        raise NotFoundError("Ticket not found")

    event = db.session.get(Event, ticket.order.event_id)
    if event is None or event.organization_id != org_id:
        raise ForbiddenError("Ticket does not belong to this organization")

    if not ticket.checked_in:
        raise ConflictError("Ticket is not checked in")

    ticket.checked_in = False
    ticket.checked_in_at = None
    db.session.commit()

    return {"data": _ticket_to_dict(ticket)}


def get_checkin_history(
    org_id: uuid.UUID,
    event_id: str,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    event = db.session.get(Event, event_id)
    if event is None or event.organization_id != org_id:
        raise NotFoundError("Event not found")

    base_query = (
        select(Ticket)
        .join(Order)
        .where(
            Ticket.order.has(Order.event_id == event_id),
            Ticket.checked_in.is_(True),
        )
    )

    total = db.session.execute(
        select(func.count()).select_from(base_query.subquery())
    ).scalar()

    tickets = db.session.execute(
        base_query
        .order_by(Ticket.checked_in_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).scalars().all()

    return {
        "data": [_ticket_to_dict(t) for t in tickets],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def search_tickets(org_id: uuid.UUID, event_id: str, query: str) -> dict:
    event = db.session.get(Event, event_id)
    if event is None or event.organization_id != org_id:
        raise NotFoundError("Event not found")

    if not query:
        raise ConflictError("Search query is required")

    pattern = f"%{query}%"
    tickets = db.session.execute(
        select(Ticket)
        .join(Order)
        .join(Attendee)
        .where(
            Ticket.order.has(Order.event_id == event_id),
            or_(
                Attendee.name.ilike(pattern),
                Attendee.email.ilike(pattern),
            ),
        )
        .order_by(Ticket.checked_in.asc(), Attendee.name.asc())
    ).scalars().all()

    return {"data": [_ticket_to_dict(t) for t in tickets]}


def get_checkin_stats(org_id: uuid.UUID, event_id: str) -> dict:
    event = db.session.get(Event, event_id)
    if event is None or event.organization_id != org_id:
        raise NotFoundError("Event not found")

    total = db.session.execute(
        select(func.count(Ticket.id))
        .join(Order)
        .where(Order.event_id == event_id, Order.status != OrderStatus.CANCELLED)
    ).scalar()

    checked_in = db.session.execute(
        select(func.count(Ticket.id))
        .join(Order)
        .where(
            Order.event_id == event_id,
            Order.status != OrderStatus.CANCELLED,
            Ticket.checked_in.is_(True),
        )
    ).scalar()

    hourly = db.session.execute(
        select(
            func.date_trunc("hour", Ticket.checked_in_at).label("hour"),
            func.count(Ticket.id).label("count"),
        )
        .join(Order)
        .where(
            Order.event_id == event_id,
            Order.status != OrderStatus.CANCELLED,
            Ticket.checked_in.is_(True),
            Ticket.checked_in_at.isnot(None),
        )
        .group_by("hour")
        .order_by("hour")
    ).all()

    return {
        "data": {
            "total": total,
            "checked_in": checked_in,
            "remaining": total - checked_in,
            "hourly": [
                {"hour": row.hour.isoformat(), "count": row.count}
                for row in hourly
            ],
        }
    }


def _ticket_to_dict(ticket: Ticket) -> dict:
    event = db.session.get(Event, ticket.order.event_id)
    attendee = db.session.get(Attendee, ticket.attendee_id)
    tt = db.session.get(TicketType, ticket.ticket_type_id)

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
        "ticket_type": tt.name if tt else None,
        "attendee": {
            "id": str(attendee.id) if attendee else None,
            "name": attendee.name if attendee else None,
            "email": attendee.email if attendee else None,
        },
    }
