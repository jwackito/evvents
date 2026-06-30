from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.extensions import db
from app.models.attendee import Attendee
from app.models.event import Event, EventStatus, TicketType
from app.models.order import Order, OrderStatus
from app.models.ticket import Ticket

MAX_TICKETS_PER_ORDER = 10


def create_order(
    event_slug: str,
    ticket_type_id: str,
    quantity: int,
    attendee_name: str,
    attendee_email: str | None = None,
    telegram_chat_id: int | None = None,
) -> dict:
    event = db.session.execute(
        select(Event).where(Event.slug == event_slug, Event.status == EventStatus.PUBLISHED)
    ).scalar_one_or_none()
    if event is None:
        raise NotFoundError("Event not found")

    ticket_type = db.session.get(TicketType, ticket_type_id)
    if ticket_type is None or ticket_type.event_id != event.id:
        raise NotFoundError("Ticket type not found")

    if quantity < 1 or quantity > ticket_type.max_per_order:
        raise ValidationError(
            f"Quantity must be between 1 and {ticket_type.max_per_order}"
        )

    if quantity > MAX_TICKETS_PER_ORDER:
        raise ValidationError(f"Cannot order more than {MAX_TICKETS_PER_ORDER} tickets at once")

    sold_count = db.session.execute(
        select(db.func.count(Ticket.id)).join(Order).where(
            Ticket.ticket_type_id == ticket_type.id,
            Order.status != OrderStatus.CANCELLED,
        )
    ).scalar()

    remaining = ticket_type.capacity - sold_count
    if quantity > remaining:
        raise ValidationError(
            f"Only {remaining} tickets remaining for {ticket_type.name}"
        )

    attendee = Attendee(
        id=uuid.uuid4(),
        name=attendee_name,
        email=attendee_email,
        telegram_chat_id=telegram_chat_id,
        link_code=_generate_link_code(),
    )
    db.session.add(attendee)

    order = Order(
        id=uuid.uuid4(),
        event_id=event.id,
        status=OrderStatus.CONFIRMED,
    )
    db.session.add(order)
    db.session.flush()

    tickets = []
    for _ in range(quantity):
        ticket = Ticket(
            id=uuid.uuid4(),
            order_id=order.id,
            ticket_type_id=ticket_type.id,
            attendee_id=attendee.id,
            qr_hash=_generate_qr_hash(),
        )
        db.session.add(ticket)
        tickets.append(ticket)

    db.session.commit()

    return {
        "data": {
            "order_id": str(order.id),
            "status": order.status.value,
            "attendee": {
                "id": str(attendee.id),
                "name": attendee.name,
                "email": attendee.email,
                "link_code": attendee.link_code,
            },
            "tickets": [
                {
                    "id": str(t.id),
                    "qr_hash": t.qr_hash,
                    "ticket_type": ticket_type.name,
                }
                for t in tickets
            ],
        }
    }


def _generate_qr_hash() -> str:
    raw = f"{uuid.uuid4()}-{secrets.token_hex(16)}-{datetime.now(timezone.utc).isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _generate_link_code() -> str:
    return secrets.token_hex(8)
