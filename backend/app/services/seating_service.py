from __future__ import annotations

import uuid

from sqlalchemy import select

from app.exceptions import NotFoundError
from app.extensions import db
from app.models.event import Event
from app.models.order import Order, OrderStatus
from app.models.ticket import Ticket


def _verify_event_ownership(event_id: uuid.UUID, org_id: uuid.UUID) -> Event:
    event = db.session.get(Event, event_id)
    if event is None or event.organization_id != org_id:
        raise NotFoundError("Event not found")
    return event


def _verify_ticket_belongs_to_event(ticket_id: uuid.UUID, event_id: uuid.UUID) -> Ticket:
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        raise NotFoundError("Ticket not found")
    order = db.session.get(Order, ticket.order_id)
    if order is None or order.event_id != event_id:
        raise NotFoundError("Ticket not found for this event")
    return ticket


def get_seating(event_id: uuid.UUID, org_id: uuid.UUID) -> dict:
    event = _verify_event_ownership(event_id, org_id)

    tickets = db.session.execute(
        select(Ticket).join(Order).where(
            Order.event_id == event.id,
            Order.status != OrderStatus.CANCELLED,
        ).order_by(Ticket.seat.asc().nullslast())
    ).scalars().all()

    return {
        "data": [
            {
                "ticket_id": str(t.id),
                "ticket_type": t.ticket_type.name if t.ticket_type else None,
                "attendee_name": t.attendee.name if t.attendee else None,
                "seat": t.seat,
                "checked_in": t.checked_in,
            }
            for t in tickets
        ]
    }


def assign_seat(event_id: uuid.UUID, ticket_id: uuid.UUID, org_id: uuid.UUID, seat: str) -> dict:
    _verify_event_ownership(event_id, org_id)
    ticket = _verify_ticket_belongs_to_event(ticket_id, event_id)

    ticket.seat = seat
    db.session.commit()

    return {
        "data": {
            "ticket_id": str(ticket.id),
            "seat": ticket.seat,
        }
    }


def release_seat(event_id: uuid.UUID, ticket_id: uuid.UUID, org_id: uuid.UUID) -> None:
    _verify_event_ownership(event_id, org_id)
    ticket = _verify_ticket_belongs_to_event(ticket_id, event_id)

    ticket.seat = None
    db.session.commit()


def bulk_assign(event_id: uuid.UUID, org_id: uuid.UUID, assignments: dict[str, str | None]) -> dict:
    _verify_event_ownership(event_id, org_id)

    results = []
    for ticket_id_str, seat in assignments.items():
        ticket = _verify_ticket_belongs_to_event(uuid.UUID(ticket_id_str), event_id)
        ticket.seat = seat
        results.append({
            "ticket_id": ticket_id_str,
            "seat": seat,
        })

    db.session.commit()

    return {"data": results}
