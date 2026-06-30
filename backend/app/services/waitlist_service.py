from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.extensions import db
from app.models.attendee import Attendee
from app.models.event import Event, EventStatus, TicketType
from app.models.order import Order, OrderStatus
from app.models.ticket import Ticket
from app.models.waitlist import WaitlistEntry


def join_waitlist(
    event_slug: str,
    ticket_type_id: str,
    attendee_name: str,
    attendee_email: str | None = None,
) -> dict:
    event = db.session.execute(
        select(Event).where(Event.slug == event_slug, Event.status == EventStatus.PUBLISHED)
    ).scalar_one_or_none()
    if event is None:
        raise NotFoundError("Event not found")

    ticket_type = db.session.get(TicketType, ticket_type_id)
    if ticket_type is None or ticket_type.event_id != event.id:
        raise NotFoundError("Ticket type not found")

    sold_count = db.session.execute(
        select(func.count(Ticket.id)).join(Order).where(
            Ticket.ticket_type_id == ticket_type.id,
            Order.status != OrderStatus.CANCELLED,
        )
    ).scalar()

    if sold_count < ticket_type.capacity:
        raise ValidationError("Tickets are still available for this ticket type")

    max_pos = db.session.execute(
        select(func.coalesce(func.max(WaitlistEntry.position), 0)).where(
            WaitlistEntry.event_id == event.id,
            WaitlistEntry.ticket_type_id == ticket_type.id,
        )
    ).scalar()

    attendee = Attendee(
        id=uuid.uuid4(),
        name=attendee_name,
        email=attendee_email,
        link_code=secrets.token_hex(8),
    )
    db.session.add(attendee)
    db.session.flush()

    entry = WaitlistEntry(
        id=uuid.uuid4(),
        event_id=event.id,
        ticket_type_id=ticket_type.id,
        attendee_id=attendee.id,
        position=max_pos + 1,
    )
    db.session.add(entry)
    db.session.commit()

    return {
        "data": {
            "id": str(entry.id),
            "position": entry.position,
            "event_title": event.title,
            "ticket_type_name": ticket_type.name,
            "attendee": {
                "id": str(attendee.id),
                "name": attendee.name,
                "email": attendee.email,
                "link_code": attendee.link_code,
            },
        }
    }


def leave_waitlist(entry_id: str, link_code: str) -> None:
    entry = db.session.get(WaitlistEntry, entry_id)
    if entry is None:
        raise NotFoundError("Waitlist entry not found")

    attendee = db.session.get(Attendee, entry.attendee_id)
    if attendee is None or attendee.link_code != link_code:
        raise ConflictError("Invalid link code")

    db.session.delete(entry)
    if attendee:
        db.session.delete(attendee)

    db.session.execute(
        db.text("""
            UPDATE waitlist_entries
            SET position = position - 1
            WHERE event_id = :event_id
              AND ticket_type_id = :tt_id
              AND position > :pos
        """),
        {"event_id": entry.event_id, "tt_id": entry.ticket_type_id, "pos": entry.position},
    )
    db.session.commit()


def get_position(event_slug: str, email: str) -> dict:
    event = db.session.execute(
        select(Event).where(Event.slug == event_slug)
    ).scalar_one_or_none()
    if event is None:
        raise NotFoundError("Event not found")

    entry = db.session.execute(
        select(WaitlistEntry).join(Attendee).where(
            WaitlistEntry.event_id == event.id,
            Attendee.email == email,
            WaitlistEntry.claimed.is_(False),
        )
    ).scalar_one_or_none()

    if entry is None:
        raise NotFoundError("No active waitlist entry found for this email")

    return {
        "data": {
            "position": entry.position,
            "event_title": event.title,
            "ticket_type_name": entry.ticket_type.name,
        }
    }


def list_event_waitlist(event_id: uuid.UUID, org_id: uuid.UUID) -> dict:
    event = db.session.get(Event, event_id)
    if event is None or event.organization_id != org_id:
        raise NotFoundError("Event not found")

    entries = db.session.execute(
        select(WaitlistEntry)
        .where(
            WaitlistEntry.event_id == event.id,
            WaitlistEntry.claimed.is_(False),
        )
        .order_by(WaitlistEntry.position)
    ).scalars().all()

    return {
        "data": [
            {
                "id": str(e.id),
                "position": e.position,
                "attendee_name": e.attendee.name if e.attendee else None,
                "attendee_email": e.attendee.email if e.attendee else None,
                "ticket_type_name": e.ticket_type.name if e.ticket_type else None,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ]
    }


def claim_entry(entry_id: uuid.UUID, org_id: uuid.UUID, event_id: uuid.UUID | None = None) -> dict:
    entry = db.session.get(WaitlistEntry, entry_id)
    if entry is None:
        raise NotFoundError("Waitlist entry not found")

    if event_id is not None and entry.event_id != event_id:
        raise NotFoundError("Waitlist entry not found for this event")

    event = db.session.get(Event, entry.event_id)
    if event is None or event.organization_id != org_id:
        raise NotFoundError("Event not found")

    if entry.claimed:
        raise ConflictError("Waitlist entry already claimed")

    entry.claimed = True
    entry.claimed_at = datetime.now(timezone.utc)
    entry.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db.session.commit()

    return {
        "data": {
            "id": str(entry.id),
            "position": entry.position,
            "claimed_at": entry.claimed_at.isoformat(),
            "expires_at": entry.expires_at.isoformat(),
            "attendee": {
                "id": str(entry.attendee.id) if entry.attendee else None,
                "name": entry.attendee.name if entry.attendee else None,
                "email": entry.attendee.email if entry.attendee else None,
                "link_code": entry.attendee.link_code if entry.attendee else None,
            },
            "ticket_type": {
                "id": str(entry.ticket_type.id) if entry.ticket_type else None,
                "name": entry.ticket_type.name if entry.ticket_type else None,
            },
        }
    }
