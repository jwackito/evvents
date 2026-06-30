from __future__ import annotations

from apiflask import APIBlueprint, Schema
from flask import request
from marshmallow import fields, validate

from app.api.decorators import require_role
from app.services.checkin_service import (
    get_checkin_events,
    get_checkin_history,
    get_checkin_stats,
    scan_ticket,
    search_tickets,
    undo_check_in,
)

checkin_bp = APIBlueprint("checkin", __name__, url_prefix="/api/v1")


class ScanInput(Schema):
    qr_hash = fields.String(required=True)


class UndoInput(Schema):
    qr_hash = fields.String(required=True)


@checkin_bp.get("/check-in/events")
@require_role("admin", "operator", "checkin_staff")
def checkin_events():
    from app.api.org import _require_org

    org_id = _require_org()
    return get_checkin_events(org_id)


@checkin_bp.post("/check-in/scan")
@checkin_bp.input(ScanInput)
@require_role("admin", "operator", "checkin_staff")
def checkin_scan(json_data):
    from app.api.org import _require_org

    org_id = _require_org()
    return scan_ticket(org_id, json_data["qr_hash"])


@checkin_bp.post("/check-in/undo")
@checkin_bp.input(UndoInput)
@require_role("admin", "operator", "checkin_staff")
def checkin_undo(json_data):
    from app.api.org import _require_org

    org_id = _require_org()
    return undo_check_in(org_id, json_data["qr_hash"])


@checkin_bp.get("/check-in/events/<event_id>/history")
@require_role("admin", "operator", "checkin_staff")
def checkin_history(event_id: str):
    from app.api.org import _require_org

    org_id = _require_org()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    return get_checkin_history(org_id, event_id, page, per_page)


@checkin_bp.get("/check-in/events/<event_id>/search")
@require_role("admin", "operator", "checkin_staff")
def checkin_search(event_id: str):
    from app.api.org import _require_org

    org_id = _require_org()
    query = request.args.get("q", "")
    return search_tickets(org_id, event_id, query)


@checkin_bp.get("/check-in/events/<event_id>/stats")
@require_role("admin", "operator", "checkin_staff")
def checkin_stats(event_id: str):
    from app.api.org import _require_org

    org_id = _require_org()
    return get_checkin_stats(org_id, event_id)
