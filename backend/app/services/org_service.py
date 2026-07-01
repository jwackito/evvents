from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.extensions import db
from app.models.event import Event, EventStatus, SeatingType, TicketType
from app.models.order import Order, OrderStatus
from app.models.organization import Organization
from app.models.ticket import Ticket


def _verify_event_ownership(event_id: uuid.UUID, org_id: uuid.UUID) -> Event:
    event = db.session.get(Event, event_id)
    if event is None or event.organization_id != org_id:
        raise NotFoundError("Event not found")
    return event


def list_org_events(
    org_id: uuid.UUID,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    query = select(Event).where(Event.organization_id == org_id)
    if status:
        try:
            status_enum = EventStatus(status)
            query = query.where(Event.status == status_enum)
        except ValueError:
            raise ValidationError(f"Invalid status: {status}")

    total = db.session.execute(
        select(func.count(Event.id)).where(Event.organization_id == org_id)
    ).scalar()

    events = db.session.execute(
        query.order_by(Event.date.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).scalars().all()

    return {
        "data": [_event_to_dict(e) for e in events],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def create_event(org_id: uuid.UUID, data: dict) -> dict:
    existing = db.session.execute(
        select(Event).where(
            Event.organization_id == org_id,
            Event.slug == data["slug"],
        )
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("An event with this slug already exists")

    event = Event(
        id=uuid.uuid4(),
        organization_id=org_id,
        title=data["title"],
        description=data.get("description"),
        date=data["date"],
        location=data.get("location"),
        capacity=data["capacity"],
        status=EventStatus(data.get("status", "draft")),
        seating_type=SeatingType(data.get("seating_type", "general")),
        slug=data["slug"],
        cover_image=data.get("cover_image"),
    )
    db.session.add(event)
    db.session.commit()

    return {"data": _event_to_dict(event)}


def get_org_event_by_slug(slug: str, org_id: uuid.UUID) -> dict:
    event = db.session.execute(
        select(Event).where(Event.slug == slug, Event.organization_id == org_id)
    ).scalar_one_or_none()
    if event is None:
        raise NotFoundError("Event not found")
    return {"data": _event_to_dict(event)}


def update_event(event_id: uuid.UUID, org_id: uuid.UUID, data: dict) -> dict:
    event = _verify_event_ownership(event_id, org_id)

    if "capacity" in data and data["capacity"] is not None:
        confirmed = db.session.execute(
            select(func.count(Ticket.id)).join(Order).where(
                Ticket.ticket_type_id.in_(
                    select(TicketType.id).where(TicketType.event_id == event.id)
                ),
                Order.status != OrderStatus.CANCELLED,
            )
        ).scalar()
        if data["capacity"] < confirmed:
            raise ValidationError(
                f"Capacity cannot be less than {confirmed} confirmed tickets"
            )

    if "slug" in data and data["slug"] != event.slug:
        existing = db.session.execute(
            select(Event).where(
                Event.slug == data["slug"],
                Event.organization_id == org_id,
                Event.id != event.id,
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictError("An event with this slug already exists")

    for field in ("title", "description", "date", "location", "capacity", "cover_image", "slug"):
        if field in data:
            setattr(event, field, data[field])

    if "status" in data:
        event.status = EventStatus(data["status"])
    if "seating_type" in data:
        event.seating_type = SeatingType(data["seating_type"])

    db.session.commit()
    return {"data": _event_to_dict(event)}


def delete_event(event_id: uuid.UUID, org_id: uuid.UUID) -> None:
    event = _verify_event_ownership(event_id, org_id)
    event.deleted_at = datetime.now(timezone.utc)
    event.status = EventStatus.CANCELLED
    db.session.commit()


def list_ticket_types(event_id: uuid.UUID, org_id: uuid.UUID) -> dict:
    event = _verify_event_ownership(event_id, org_id)
    return {
        "data": [
            {
                "id": str(tt.id),
                "name": tt.name,
                "description": tt.description,
                "price": tt.price,
                "capacity": tt.capacity,
                "max_per_order": tt.max_per_order,
            }
            for tt in event.ticket_types
        ]
    }


def create_ticket_type(event_id: uuid.UUID, org_id: uuid.UUID, data: dict) -> dict:
    event = _verify_event_ownership(event_id, org_id)

    tt = TicketType(
        id=uuid.uuid4(),
        event_id=event.id,
        name=data["name"],
        description=data.get("description"),
        price=data.get("price", 0),
        capacity=data["capacity"],
        max_per_order=data.get("max_per_order", 5),
    )
    db.session.add(tt)
    db.session.commit()

    return {
        "data": {
            "id": str(tt.id),
            "name": tt.name,
            "description": tt.description,
            "price": tt.price,
            "capacity": tt.capacity,
            "max_per_order": tt.max_per_order,
        }
    }, 201


def update_ticket_type(event_id: uuid.UUID, tt_id: uuid.UUID, org_id: uuid.UUID, data: dict) -> dict:
    _verify_event_ownership(event_id, org_id)
    tt = db.session.get(TicketType, tt_id)
    if tt is None or tt.event_id != event_id:
        raise NotFoundError("Ticket type not found")

    for field in ("name", "description", "price", "capacity", "max_per_order"):
        if field in data:
            setattr(tt, field, data[field])

    db.session.commit()
    return {
        "data": {
            "id": str(tt.id),
            "name": tt.name,
            "description": tt.description,
            "price": tt.price,
            "capacity": tt.capacity,
            "max_per_order": tt.max_per_order,
        }
    }


def delete_ticket_type(event_id: uuid.UUID, tt_id: uuid.UUID, org_id: uuid.UUID) -> None:
    _verify_event_ownership(event_id, org_id)
    tt = db.session.get(TicketType, tt_id)
    if tt is None or tt.event_id != event_id:
        raise NotFoundError("Ticket type not found")

    tickets_count = db.session.execute(
        select(func.count(Ticket.id)).where(Ticket.ticket_type_id == tt.id)
    ).scalar()
    if tickets_count > 0:
        raise ConflictError("Cannot delete ticket type with existing tickets")

    db.session.delete(tt)
    db.session.commit()


def get_event_orders(event_id: uuid.UUID, org_id: uuid.UUID) -> dict:
    event = _verify_event_ownership(event_id, org_id)
    orders = db.session.execute(
        select(Order).where(Order.event_id == event.id).order_by(Order.created_at.desc())
    ).scalars().all()

    return {
        "data": [
            {
                "id": str(o.id),
                "status": o.status.value,
                "created_at": o.created_at.isoformat(),
                "ticket_count": len(o.tickets),
            }
            for o in orders
        ]
    }


def get_event_stats(event_id: uuid.UUID, org_id: uuid.UUID) -> dict:
    event = _verify_event_ownership(event_id, org_id)

    total_orders = db.session.execute(
        select(func.count(Order.id)).where(Order.event_id == event.id)
    ).scalar()

    total_tickets = db.session.execute(
        select(func.count(Ticket.id)).join(Order).where(
            Ticket.ticket_type_id.in_(
                select(TicketType.id).where(TicketType.event_id == event.id)
            ),
            Order.status != OrderStatus.CANCELLED,
        )
    ).scalar()

    checked_in = db.session.execute(
        select(func.count(Ticket.id)).join(Order).where(
            Ticket.ticket_type_id.in_(
                select(TicketType.id).where(TicketType.event_id == event.id)
            ),
            Order.status != OrderStatus.CANCELLED,
            Ticket.checked_in.is_(True),
        )
    ).scalar()

    return {
        "data": {
            "total_orders": total_orders,
            "total_tickets": total_tickets,
            "checked_in": checked_in,
            "remaining": event.capacity - (total_tickets or 0),
            "capacity": event.capacity,
        }
    }


def update_bot_config(org_id: uuid.UUID, data: dict) -> dict:
    org = db.session.get(Organization, org_id)
    if org is None:
        raise NotFoundError("Organization not found")

    if "telegram_bot_token" in data:
        org.telegram_bot_token = data["telegram_bot_token"]
    if "telegram_webhook_url" in data:
        org.telegram_webhook_url = data["telegram_webhook_url"]

    db.session.commit()
    return {"data": {"message": "Bot config updated"}}


def list_checkin_events(org_id: uuid.UUID) -> dict:
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


def _event_to_dict(event: Event) -> dict:
    return {
        "id": str(event.id),
        "title": event.title,
        "description": event.description,
        "date": event.date.isoformat(),
        "location": event.location,
        "capacity": event.capacity,
        "status": event.status.value,
        "seating_type": event.seating_type.value,
        "slug": event.slug,
        "cover_image": event.cover_image,
        "ticket_types": [
            {
                "id": str(tt.id),
                "name": tt.name,
                "description": tt.description,
                "price": tt.price,
                "capacity": tt.capacity,
                "max_per_order": tt.max_per_order,
            }
            for tt in event.ticket_types
        ],
    }
