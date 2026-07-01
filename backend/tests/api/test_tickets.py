from __future__ import annotations

import uuid

URL = "/api/v1/tickets"


def test_lookup_found(client, created_order):
    _, _, ticket = created_order
    resp = client.get(f"{URL}/{ticket.qr_hash}")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["qr_hash"] == ticket.qr_hash
    assert data["checked_in"] is False
    assert data["event"]["title"] == "Python Conference"
    assert data["attendee"]["name"] == "John Doe"


def test_lookup_not_found(client):
    resp = client.get(f"{URL}/{'b' * 64}")
    assert resp.status_code == 404


def test_check_in_success(client, created_order):
    _, _, ticket = created_order
    resp = client.post(f"{URL}/check-in", json={"qr_hash": ticket.qr_hash},
                       headers=_admin_headers(client))
    assert resp.status_code == 200
    assert resp.get_json()["data"]["checked_in"] is True


def test_check_in_already_done(client, created_order):
    _, _, ticket = created_order
    client.post(f"{URL}/check-in", json={"qr_hash": ticket.qr_hash},
                headers=_admin_headers(client))
    resp = client.post(f"{URL}/check-in", json={"qr_hash": ticket.qr_hash},
                       headers=_admin_headers(client))
    assert resp.status_code == 409
    assert resp.get_json()["code"] == "CONFLICT"


def test_check_in_not_found(client):
    resp = client.post(f"{URL}/check-in", json={"qr_hash": "b" * 64},
                       headers=_admin_headers(client))
    assert resp.status_code == 404


def test_check_in_no_auth(client, created_order):
    _, _, ticket = created_order
    resp = client.post(f"{URL}/check-in", json={"qr_hash": ticket.qr_hash})
    assert resp.status_code == 401


def test_link_success(client, created_order):
    _, attendee, ticket = created_order
    resp = client.post(f"{URL}/link", json={
        "qr_hash": ticket.qr_hash,
        "link_code": attendee.link_code,
    })
    assert resp.status_code == 200


def test_link_invalid_code(client, created_order):
    _, _, ticket = created_order
    resp = client.post(f"{URL}/link", json={
        "qr_hash": ticket.qr_hash,
        "link_code": "wrong-code",
    })
    assert resp.status_code == 409


def test_link_not_found(client):
    resp = client.post(f"{URL}/link", json={
        "qr_hash": "b" * 64,
        "link_code": "test",
    })
    assert resp.status_code == 404


def test_my_orders_success(client, db, published_event, ticket_type):
    email = f"user-{uuid.uuid4().hex[:8]}@test.com"
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "name": "Test User",
    })
    token = reg.get_json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    from tests.factories import AttendeeFactory, OrderFactory, TicketFactory
    from app.models.order import OrderStatus

    attendee = AttendeeFactory(email=email, name="Test User")
    order = OrderFactory(event=published_event, status=OrderStatus.CONFIRMED)
    TicketFactory(order=order, attendee=attendee, ticket_type=ticket_type, qr_hash="z" * 64)

    resp = client.get("/api/v1/me/orders", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data) == 1
    assert data[0]["order_id"] == str(order.id)
    assert data[0]["event_title"] == published_event.title


def test_my_orders_empty(client):
    email = f"user-{uuid.uuid4().hex[:8]}@test.com"
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "name": "Test User",
    })
    token = reg.get_json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/me/orders", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"] == []


def test_my_orders_no_auth(client):
    resp = client.get("/api/v1/me/orders")
    assert resp.status_code == 401


def _admin_headers(client):
    email = f"admin-{uuid.uuid4().hex[:8]}@test.com"
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "name": "Admin",
    })
    token = reg.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
