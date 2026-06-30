from __future__ import annotations

import uuid
from datetime import datetime, timezone

URL = "/api/v1/check-in"


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Events ---


def test_checkin_events_list(client, checkin_token, published_event):
    resp = client.get(f"{URL}/events", headers=_headers(checkin_token))
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data) == 1
    assert data[0]["title"] == "Python Conference"


def test_checkin_events_empty(client, checkin_token, db):
    resp = client.get(f"{URL}/events", headers=_headers(checkin_token))
    assert resp.status_code == 200
    assert resp.get_json()["data"] == []


def test_checkin_events_no_auth(client):
    resp = client.get(f"{URL}/events")
    assert resp.status_code == 401


def test_checkin_events_no_org(client, no_org_token):
    resp = client.get(f"{URL}/events", headers=_headers(no_org_token))
    assert resp.status_code == 403


# --- Scan ---


def test_scan_success(client, checkin_token, created_order):
    _, _, ticket = created_order
    resp = client.post(f"{URL}/scan", json={"qr_hash": ticket.qr_hash},
                       headers=_headers(checkin_token))
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["checked_in"] is True
    assert data["checked_in_at"] is not None


def test_scan_not_found(client, checkin_token):
    resp = client.post(f"{URL}/scan", json={"qr_hash": "b" * 64},
                       headers=_headers(checkin_token))
    assert resp.status_code == 404


def test_scan_already_checked(client, checkin_token, created_order):
    _, _, ticket = created_order
    client.post(f"{URL}/scan", json={"qr_hash": ticket.qr_hash},
                headers=_headers(checkin_token))
    resp = client.post(f"{URL}/scan", json={"qr_hash": ticket.qr_hash},
                       headers=_headers(checkin_token))
    assert resp.status_code == 409


def test_scan_wrong_org(client, checkin_token, created_order, db):
    from app.models.organization import Organization

    other_org = Organization(id=uuid.uuid4(), name="Other", slug="other")
    db.session.add(other_org)
    db.session.commit()

    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    from app.utils.jwt import create_access_token

    other_user = User(
        id=uuid.uuid4(), email="other@test.com",
        password_hash=hash_password("password123"), name="Other",
        role=UserRole.CHECKIN_STAFF, organization_id=other_org.id,
    )
    db.session.add(other_user)
    db.session.commit()
    other_token = create_access_token(other_user.id, {"role": other_user.role.value})

    _, _, ticket = created_order
    resp = client.post(f"{URL}/scan", json={"qr_hash": ticket.qr_hash},
                       headers=_headers(other_token))
    assert resp.status_code == 403


def test_scan_no_auth(client, created_order):
    _, _, ticket = created_order
    resp = client.post(f"{URL}/scan", json={"qr_hash": ticket.qr_hash})
    assert resp.status_code == 401


# --- Undo ---


def test_undo_success(client, checkin_token, created_order):
    _, _, ticket = created_order
    client.post(f"{URL}/scan", json={"qr_hash": ticket.qr_hash},
                headers=_headers(checkin_token))
    resp = client.post(f"{URL}/undo", json={"qr_hash": ticket.qr_hash},
                       headers=_headers(checkin_token))
    assert resp.status_code == 200
    assert resp.get_json()["data"]["checked_in"] is False


def test_undo_not_checked_in(client, checkin_token, created_order):
    _, _, ticket = created_order
    resp = client.post(f"{URL}/undo", json={"qr_hash": ticket.qr_hash},
                       headers=_headers(checkin_token))
    assert resp.status_code == 409


def test_undo_not_found(client, checkin_token):
    resp = client.post(f"{URL}/undo", json={"qr_hash": "b" * 64},
                       headers=_headers(checkin_token))
    assert resp.status_code == 404


def test_undo_wrong_org(client, checkin_token, created_order, db):
    from app.models.organization import Organization
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    from app.utils.jwt import create_access_token

    other_org = Organization(id=uuid.uuid4(), name="Other", slug="other")
    db.session.add(other_org)
    db.session.commit()

    other_user = User(
        id=uuid.uuid4(), email="other@test.com",
        password_hash=hash_password("password123"), name="Other",
        role=UserRole.CHECKIN_STAFF, organization_id=other_org.id,
    )
    db.session.add(other_user)
    db.session.commit()
    other_token = create_access_token(other_user.id, {"role": other_user.role.value})

    _, _, ticket = created_order
    resp = client.post(f"{URL}/undo", json={"qr_hash": ticket.qr_hash},
                       headers=_headers(other_token))
    assert resp.status_code == 403


# --- History ---


def test_history_empty(client, checkin_token, published_event):
    resp = client.get(f"{URL}/events/{published_event.id}/history",
                      headers=_headers(checkin_token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["data"] == []
    assert data["total"] == 0


def test_history_with_data(client, checkin_token, created_order, published_event):
    _, _, ticket = created_order
    client.post(f"{URL}/scan", json={"qr_hash": ticket.qr_hash},
                headers=_headers(checkin_token))
    resp = client.get(f"{URL}/events/{published_event.id}/history",
                      headers=_headers(checkin_token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["data"]) == 1
    assert data["total"] == 1
    assert data["data"][0]["checked_in"] is True


def test_history_not_found(client, checkin_token):
    resp = client.get(f"{URL}/events/{uuid.uuid4()}/history",
                      headers=_headers(checkin_token))
    assert resp.status_code == 404


# --- Search ---


def test_search_by_name(client, checkin_token, created_order, published_event):
    _, _, ticket = created_order
    resp = client.get(f"{URL}/events/{published_event.id}/search?q=John",
                      headers=_headers(checkin_token))
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data) == 1
    assert data[0]["attendee"]["name"] == "John Doe"


def test_search_by_email(client, checkin_token, created_order, published_event):
    resp = client.get(f"{URL}/events/{published_event.id}/search?q=john@test.com",
                      headers=_headers(checkin_token))
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) == 1


def test_search_no_match(client, checkin_token, published_event):
    resp = client.get(f"{URL}/events/{published_event.id}/search?q=ZZZZ",
                      headers=_headers(checkin_token))
    assert resp.status_code == 200
    assert resp.get_json()["data"] == []


def test_search_empty_query(client, checkin_token, published_event):
    resp = client.get(f"{URL}/events/{published_event.id}/search?q=",
                      headers=_headers(checkin_token))
    assert resp.status_code == 409


def test_search_not_found_event(client, checkin_token):
    resp = client.get(f"{URL}/events/{uuid.uuid4()}/search?q=John",
                      headers=_headers(checkin_token))
    assert resp.status_code == 404


# --- Stats ---


def test_stats_with_data(client, checkin_token, created_order, published_event):
    _, _, ticket = created_order
    client.post(f"{URL}/scan", json={"qr_hash": ticket.qr_hash},
                headers=_headers(checkin_token))
    resp = client.get(f"{URL}/events/{published_event.id}/stats",
                      headers=_headers(checkin_token))
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["total"] >= 1
    assert data["checked_in"] == 1
    assert data["hourly"] != []


def test_stats_no_checkins(client, checkin_token, created_order, published_event):
    resp = client.get(f"{URL}/events/{published_event.id}/stats",
                      headers=_headers(checkin_token))
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["checked_in"] == 0
    assert data["hourly"] == []


def test_stats_not_found(client, checkin_token):
    resp = client.get(f"{URL}/events/{uuid.uuid4()}/stats",
                      headers=_headers(checkin_token))
    assert resp.status_code == 404


# --- RBAC ---


def test_operator_can_scan(client, operator_token, created_order):
    _, _, ticket = created_order
    resp = client.post(f"{URL}/scan", json={"qr_hash": ticket.qr_hash},
                       headers=_headers(operator_token))
    assert resp.status_code == 200


def test_operator_can_undo(client, operator_token, created_order):
    _, _, ticket = created_order
    client.post(f"{URL}/scan", json={"qr_hash": ticket.qr_hash},
                headers=_headers(operator_token))
    resp = client.post(f"{URL}/undo", json={"qr_hash": ticket.qr_hash},
                       headers=_headers(operator_token))
    assert resp.status_code == 200


def test_admin_can_list_events(client, admin_token, published_event):
    resp = client.get(f"{URL}/events", headers=_headers(admin_token))
    assert resp.status_code == 200
