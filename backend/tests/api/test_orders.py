from __future__ import annotations


def test_create_order_success(client, published_event, ticket_type):
    resp = client.post(f"/api/v1/events/{published_event.slug}/order", json={
        "ticket_type_id": str(ticket_type.id),
        "quantity": 2,
        "attendee_name": "John Doe",
        "attendee_email": "john@test.com",
    })
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["status"] == "confirmed"
    assert len(data["tickets"]) == 2
    assert data["attendee"]["name"] == "John Doe"
    for t in data["tickets"]:
        assert len(t["qr_hash"]) == 64


def test_create_order_minimal(client, published_event, ticket_type):
    resp = client.post(f"/api/v1/events/{published_event.slug}/order", json={
        "ticket_type_id": str(ticket_type.id),
        "quantity": 1,
        "attendee_name": "Jane",
    })
    assert resp.status_code == 201
    assert len(resp.get_json()["data"]["tickets"]) == 1


def test_create_order_unknown_event(client, ticket_type):
    resp = client.post("/api/v1/events/nonexistent/order", json={
        "ticket_type_id": str(ticket_type.id),
        "quantity": 1,
        "attendee_name": "X",
    })
    assert resp.status_code == 404


def test_create_order_unknown_ticket_type(client, published_event):
    resp = client.post(f"/api/v1/events/{published_event.slug}/order", json={
        "ticket_type_id": "00000000-0000-0000-0000-000000000000",
        "quantity": 1,
        "attendee_name": "X",
    })
    assert resp.status_code == 404


def test_create_order_exceeds_max_per_order(client, published_event, ticket_type):
    resp = client.post(f"/api/v1/events/{published_event.slug}/order", json={
        "ticket_type_id": str(ticket_type.id),
        "quantity": 10,
        "attendee_name": "X",
    })
    assert resp.status_code == 422


def test_create_order_exceeds_capacity(client, published_event, ticket_type):
    ticket_type.capacity = 1
    from app.extensions import db
    db.session.commit()

    resp = client.post(f"/api/v1/events/{published_event.slug}/order", json={
        "ticket_type_id": str(ticket_type.id),
        "quantity": 2,
        "attendee_name": "X",
    })
    assert resp.status_code == 422


def test_create_order_quantity_zero(client, published_event, ticket_type):
    resp = client.post(f"/api/v1/events/{published_event.slug}/order", json={
        "ticket_type_id": str(ticket_type.id),
        "quantity": 0,
        "attendee_name": "X",
    })
    assert resp.status_code == 422
