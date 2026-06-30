from __future__ import annotations

from apiflask import APIBlueprint
from flask import request

from app.services.event_service import get_event_by_slug, list_published_events

events_bp = APIBlueprint("events", __name__, url_prefix="/api/v1")


@events_bp.get("/events")
def list_events():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    return list_published_events(page=page, per_page=per_page)


@events_bp.get("/events/<slug>")
def event_detail(slug: str):
    return get_event_by_slug(slug)
