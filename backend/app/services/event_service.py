from __future__ import annotations

from sqlalchemy import func, select

from app.exceptions import NotFoundError
from app.extensions import db
from app.models.event import Event, EventStatus

MAX_PER_PAGE = 100
DEFAULT_PER_PAGE = 20


def list_published_events(page: int = 1, per_page: int = DEFAULT_PER_PAGE) -> dict:
    per_page = min(max(per_page, 1), MAX_PER_PAGE)
    page = max(page, 1)

    total = db.session.execute(
        select(func.count(Event.id)).where(Event.status == EventStatus.PUBLISHED)
    ).scalar()

    events = db.session.execute(
        select(Event)
        .where(Event.status == EventStatus.PUBLISHED)
        .order_by(Event.date.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).scalars().all()

    return {
        "data": [_event_to_dict(e) for e in events],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def get_event_by_slug(slug: str) -> dict:
    event = db.session.execute(
        select(Event).where(Event.slug == slug, Event.status == EventStatus.PUBLISHED)
    ).scalar_one_or_none()

    if event is None:
        raise NotFoundError("Event not found")

    return {"data": _event_to_dict(event)}


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
