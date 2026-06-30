from __future__ import annotations

import uuid

from sqlalchemy import select

from app.extensions import db
from app.models.attendee import Attendee
from app.models.event import Event, EventStatus, TicketType
from app.models.organization import Organization
from app.models.ticket import Ticket


def link_attendee(link_code: str, chat_id: int) -> Attendee | None:
    attendee = db.session.execute(
        select(Attendee).where(Attendee.link_code == link_code)
    ).scalar_one_or_none()
    if attendee is None:
        return None

    attendee.telegram_chat_id = chat_id
    attendee.telegram_linked = True
    db.session.commit()
    return attendee


def get_attendee_tickets(chat_id: int) -> list[dict]:
    tickets = db.session.execute(
        select(Ticket).join(Attendee).where(Attendee.telegram_chat_id == chat_id)
    ).scalars().all()

    results = []
    for ticket in tickets:
        event = db.session.get(Event, ticket.order.event_id)
        tt = db.session.get(TicketType, ticket.ticket_type_id)
        attendee = db.session.get(Attendee, ticket.attendee_id)
        results.append({
            "id": str(ticket.id),
            "qr_hash": ticket.qr_hash,
            "seat": ticket.seat,
            "checked_in": ticket.checked_in,
            "event_title": event.title if event else None,
            "event_date": event.date.isoformat() if event and event.date else None,
            "event_location": event.location if event else None,
            "ticket_type_name": tt.name if tt else None,
            "attendee_name": attendee.name if attendee else None,
        })
    return results


def get_org_events(org_id: uuid.UUID) -> list[dict]:
    events = db.session.execute(
        select(Event)
        .where(
            Event.organization_id == org_id,
            Event.status == EventStatus.PUBLISHED,
            Event.deleted_at.is_(None),
        )
        .order_by(Event.date.asc())
    ).scalars().all()

    return [
        {
            "id": str(e.id),
            "title": e.title,
            "date": e.date.isoformat(),
            "location": e.location,
            "slug": e.slug,
        }
        for e in events
    ]


def get_org_by_bot_token(token: str) -> Organization | None:
    return db.session.execute(
        select(Organization).where(Organization.telegram_bot_token == token)
    ).scalar_one_or_none()


def get_bot_token_orgs() -> list[Organization]:
    return db.session.execute(
        select(Organization).where(
            Organization.telegram_bot_token.isnot(None),
            Organization.telegram_bot_token != "",
            Organization.deleted_at.is_(None),
        )
    ).scalars().all()
