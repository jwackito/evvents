from __future__ import annotations

from apiflask import APIBlueprint

admin_bp = APIBlueprint("admin", __name__, url_prefix="/api/v1/admin")
