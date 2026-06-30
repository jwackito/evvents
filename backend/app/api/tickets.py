from __future__ import annotations

from apiflask import APIBlueprint

tickets_bp = APIBlueprint("tickets", __name__, url_prefix="/api/v1")
