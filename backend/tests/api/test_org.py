from __future__ import annotations

URL = "/api/v1/org"


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_list_events(client, org, published_event, admin_token):
    resp = client.get(f"{URL}/events", headers=_headers(admin_token))
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 1
    assert body["data"][0]["slug"] == published_event.slug


def test_create_event(client, admin_token):
    resp = client.post(f"{URL}/events", json={
        "title": "New Event",
        "date": "2026-12-01T10:00:00+00:00",
        "capacity": 200,
        "slug": "new-event",
    }, headers=_headers(admin_token))
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["title"] == "New Event"
    assert data["status"] == "draft"


def test_create_event_duplicate_slug(client, admin_token, published_event):
    resp = client.post(f"{URL}/events", json={
        "title": "Duplicate",
        "date": "2026-12-01T10:00:00+00:00",
        "capacity": 100,
        "slug": published_event.slug,
    }, headers=_headers(admin_token))
    assert resp.status_code == 409


def test_update_event(client, admin_token, published_event):
    resp = client.put(f"{URL}/events/{published_event.id}", json={
        "title": "Updated Title",
    }, headers=_headers(admin_token))
    assert resp.status_code == 200
    assert resp.get_json()["data"]["title"] == "Updated Title"


def test_update_event_status(client, admin_token, published_event):
    resp = client.put(f"{URL}/events/{published_event.id}", json={
        "status": "cancelled",
    }, headers=_headers(admin_token))
    assert resp.status_code == 200
    assert resp.get_json()["data"]["status"] == "cancelled"


def test_get_event_detail(client, admin_token, draft_event):
    resp = client.get(f"{URL}/events/{draft_event.slug}", headers=_headers(admin_token))
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["id"] == str(draft_event.id)
    assert data["status"] == "draft"


def test_get_event_detail_not_found(client, admin_token):
    resp = client.get(f"{URL}/events/non-existent-slug", headers=_headers(admin_token))
    assert resp.status_code == 404


def test_delete_event(client, admin_token, published_event):
    resp = client.delete(f"{URL}/events/{published_event.id}", headers=_headers(admin_token))
    assert resp.status_code == 204


def test_create_ticket_type(client, admin_token, published_event):
    resp = client.post(f"{URL}/events/{published_event.id}/ticket-types", json={
        "name": "VIP",
        "capacity": 50,
    }, headers=_headers(admin_token))
    assert resp.status_code == 201
    assert resp.get_json()["data"]["name"] == "VIP"


def test_update_ticket_type(client, admin_token, published_event, ticket_type):
    resp = client.put(
        f"{URL}/events/{published_event.id}/ticket-types/{ticket_type.id}",
        json={"name": "Premium"},
        headers=_headers(admin_token),
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["name"] == "Premium"


def test_delete_ticket_type(client, admin_token, published_event, vip_ticket_type):
    resp = client.delete(
        f"{URL}/events/{published_event.id}/ticket-types/{vip_ticket_type.id}",
        headers=_headers(admin_token),
    )
    assert resp.status_code == 204


def test_event_stats(client, admin_token, published_event):
    resp = client.get(f"{URL}/events/{published_event.id}/stats", headers=_headers(admin_token))
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["capacity"] == 500
    assert data["total_tickets"] == 0


def test_event_orders(client, admin_token, published_event):
    resp = client.get(f"{URL}/events/{published_event.id}/orders", headers=_headers(admin_token))
    assert resp.status_code == 200


def test_bot_config(client, admin_token):
    resp = client.put(f"{URL}/bot-config", json={
        "telegram_bot_token": "123:abc",
    }, headers=_headers(admin_token))
    assert resp.status_code == 200


def test_checkin_list(client, admin_token):
    resp = client.get(f"{URL}/check-in", headers=_headers(admin_token))
    assert resp.status_code == 200


def test_operator_can_create_event(client, operator_token):
    resp = client.post(f"{URL}/events", json={
        "title": "Operator Event",
        "date": "2026-12-01T10:00:00+00:00",
        "capacity": 100,
        "slug": "operator-event",
    }, headers=_headers(operator_token))
    assert resp.status_code == 201


def test_operator_cannot_delete_event(client, operator_token, published_event):
    resp = client.delete(f"{URL}/events/{published_event.id}", headers=_headers(operator_token))
    assert resp.status_code == 403


def test_checkin_staff_cannot_create_event(client, checkin_token):
    resp = client.post(f"{URL}/events", json={
        "title": "Staff Event",
        "date": "2026-12-01T10:00:00+00:00",
        "capacity": 100,
        "slug": "staff-event",
    }, headers=_headers(checkin_token))
    assert resp.status_code == 403


def test_checkin_staff_can_list_events(client, checkin_token):
    resp = client.get(f"{URL}/events", headers=_headers(checkin_token))
    assert resp.status_code == 200


def test_no_org_returns_forbidden(client, no_org_token):
    resp = client.get(f"{URL}/events", headers=_headers(no_org_token))
    assert resp.status_code == 403


def test_no_auth_returns_unauthorized(client):
    resp = client.get(f"{URL}/events")
    assert resp.status_code == 401
