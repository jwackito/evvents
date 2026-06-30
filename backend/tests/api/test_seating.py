from __future__ import annotations

import uuid

import pytest
from flask.testing import FlaskClient

from app.extensions import db as _db
from app.models.attendee import Attendee
from app.models.event import Event
from app.models.order import Order, OrderStatus
from app.models.ticket import Ticket

URL = "/api/v1/org"


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seated_order(db, published_event, ticket_type) -> tuple[Order, Attendee, Ticket]:
    attendee = Attendee(
        id=uuid.uuid4(),
        name="Seated Person",
        email="seated@test.com",
        link_code="seat-link",
    )
    db.session.add(attendee)
    db.session.flush()

    order = Order(
        id=uuid.uuid4(),
        event_id=published_event.id,
        status=OrderStatus.CONFIRMED,
    )
    db.session.add(order)
    db.session.flush()

    ticket = Ticket(
        id=uuid.uuid4(),
        order_id=order.id,
        ticket_type_id=ticket_type.id,
        attendee_id=attendee.id,
        qr_hash="z" * 64,
    )
    db.session.add(ticket)
    db.session.commit()
    return order, attendee, ticket


# --- Get Seating ---


def test_get_seating_empty(client, admin_token, published_event):
    resp = client.get(
        f"{URL}/events/{published_event.id}/seating",
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"] == []


def test_get_seating_with_data(client, admin_token, published_event, seated_order):
    _, _, ticket = seated_order
    resp = client.put(
        f"{URL}/events/{published_event.id}/seating/{ticket.id}",
        json={"seat": "A1"},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200

    resp = client.get(
        f"{URL}/events/{published_event.id}/seating",
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    seats = [s for s in resp.get_json()["data"] if s["seat"] is not None]
    assert len(seats) == 1
    assert seats[0]["seat"] == "A1"


def test_get_seating_not_found(client, admin_token):
    resp = client.get(
        f"{URL}/events/{uuid.uuid4()}/seating",
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 404


# --- Assign Seat ---


def test_assign_seat(client, admin_token, published_event, seated_order):
    _, _, ticket = seated_order
    resp = client.put(
        f"{URL}/events/{published_event.id}/seating/{ticket.id}",
        json={"seat": "B2"},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["seat"] == "B2"


def test_assign_seat_ticket_not_found(client, admin_token, published_event):
    resp = client.put(
        f"{URL}/events/{published_event.id}/seating/{uuid.uuid4()}",
        json={"seat": "A1"},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 404


def test_assign_seat_event_not_found(client, admin_token, seated_order):
    _, _, ticket = seated_order
    resp = client.put(
        f"{URL}/events/{uuid.uuid4()}/seating/{ticket.id}",
        json={"seat": "A1"},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 404


def test_assign_seat_reassign(client, admin_token, published_event, seated_order):
    _, _, ticket = seated_order
    client.put(
        f"{URL}/events/{published_event.id}/seating/{ticket.id}",
        json={"seat": "A1"},
        headers=_auth_header(admin_token),
    )
    resp = client.put(
        f"{URL}/events/{published_event.id}/seating/{ticket.id}",
        json={"seat": "C3"},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["seat"] == "C3"


# --- Release Seat ---


def test_release_seat(client, admin_token, published_event, seated_order):
    _, _, ticket = seated_order
    client.put(
        f"{URL}/events/{published_event.id}/seating/{ticket.id}",
        json={"seat": "A1"},
        headers=_auth_header(admin_token),
    )
    resp = client.delete(
        f"{URL}/events/{published_event.id}/seating/{ticket.id}",
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 204


def test_release_seat_not_found(client, admin_token, published_event):
    resp = client.delete(
        f"{URL}/events/{published_event.id}/seating/{uuid.uuid4()}",
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 404


# --- Bulk Assign ---


def test_bulk_assign(client, admin_token, published_event, seated_order, created_order):
    _, _, ticket1 = seated_order
    _, _, ticket2 = created_order

    resp = client.put(
        f"{URL}/events/{published_event.id}/seating/bulk",
        json={"assignments": {str(ticket1.id): "A1", str(ticket2.id): "B2"}},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data) == 2
    assert {d["seat"] for d in data} == {"A1", "B2"}


def test_bulk_assign_release(client, admin_token, published_event, seated_order):
    _, _, ticket = seated_order
    resp = client.put(
        f"{URL}/events/{published_event.id}/seating/bulk",
        json={"assignments": {str(ticket.id): None}},
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"][0]["seat"] is None


# --- RBAC ---


def test_checkin_staff_can_get_seating(client, checkin_token, published_event):
    resp = client.get(
        f"{URL}/events/{published_event.id}/seating",
        headers=_auth_header(checkin_token),
    )
    assert resp.status_code == 200


def test_checkin_staff_cannot_assign_seat(client, checkin_token, published_event, seated_order):
    _, _, ticket = seated_order
    resp = client.put(
        f"{URL}/events/{published_event.id}/seating/{ticket.id}",
        json={"seat": "A1"},
        headers=_auth_header(checkin_token),
    )
    assert resp.status_code == 403
