from __future__ import annotations

from apiflask import APIBlueprint

checkin_bp = APIBlueprint("checkin", __name__, url_prefix="/api/v1")
