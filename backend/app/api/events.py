from __future__ import annotations

from apiflask import APIBlueprint

events_bp = APIBlueprint("events", __name__, url_prefix="/api/v1")
