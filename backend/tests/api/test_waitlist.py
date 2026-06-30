from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from flask.testing import FlaskClient

from app.extensions import db as _db
from app.models.attendee import Attendee
from app.models.event import Event, EventStatus, SeatingType, TicketType
from app.models.order import Order, OrderStatus
from app.models.organization import Organization
from app.models.ticket import Ticket
from app.models.waitlist import WaitlistEntry

WL_URL = "/api/v1"


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sold_out_event(db, org) -> Event:
    event = Event(
        id=uuid.uuid4(),
        organization_id=org.id,
        title="Sold Out Event",
        date=datetime(2026, 12, 1, 10, 0, tzinfo=timezone.utc),
        capacity=1,
        status=EventStatus.PUBLISHED,
        seating_type=SeatingType.GENERAL,
        slug="sold-out-event",
    )
    db.session.add(event)
    db.session.commit()
    return event


@pytest.fixture
def sold_out_ticket_type(db, sold_out_event) -> TicketType:
    tt = TicketType(
        id=uuid.uuid4(),
        event_id=sold_out_event.id,
        name="Standard",
        capacity=1,
        max_per_order=1,
    )
    db.session.add(tt)
    db.session.commit()
    return tt


@pytest.fixture
def sold_out_order(db, sold_out_event, sold_out_ticket_type) -> tuple[Order, Attendee, Ticket]:
    attendee = Attendee(
        id=uuid.uuid4(),
        name="Buyer",
        email="buyer@test.com",
        link_code="buyer-link",
    )
    db.session.add(attendee)
    db.session.flush()

    order = Order(
        id=uuid.uuid4(),
        event_id=sold_out_event.id,
        status=OrderStatus.CONFIRMED,
    )
    db.session.add(order)
    db.session.flush()

    ticket = Ticket(
        id=uuid.uuid4(),
        order_id=order.id,
        ticket_type_id=sold_out_ticket_type.id,
        attendee_id=attendee.id,
        qr_hash="s" * 64,
    )
    db.session.add(ticket)
    db.session.commit()
    return order, attendee, ticket


# --- Public: Join Waitlist ---


def test_join_waitlist_success(client, sold_out_event, sold_out_ticket_type, sold_out_order):
    resp = client.post(f"{WL_URL}/events/{sold_out_event.slug}/waitlist", json={
        "ticket_type_id": str(sold_out_ticket_type.id),
        "attendee_name": "Alice",
        "attendee_email": "alice@test.com",
    })
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["position"] == 1
    assert data["attendee"]["name"] == "Alice"
    assert data["attendee"]["link_code"] is not None


def test_join_waitlist_increments_position(client, sold_out_event, sold_out_ticket_type, sold_out_order):
    for i in range(3):
        resp = client.post(f"{WL_URL}/events/{sold_out_event.slug}/waitlist", json={
            "ticket_type_id": str(sold_out_ticket_type.id),
            "attendee_name": f"Person {i}",
            "attendee_email": f"p{i}@test.com",
        })
        assert resp.status_code == 201
        assert resp.get_json()["data"]["position"] == i + 1


def test_join_waitlist_tickets_still_available(client, published_event, ticket_type):
    resp = client.post(f"{WL_URL}/events/{published_event.slug}/waitlist", json={
        "ticket_type_id": str(ticket_type.id),
        "attendee_name": "Bob",
        "attendee_email": "bob@test.com",
    })
    assert resp.status_code == 422


def test_join_waitlist_unknown_event(client, sold_out_ticket_type):
    resp = client.post(f"{WL_URL}/events/nonexistent/waitlist", json={
        "ticket_type_id": str(sold_out_ticket_type.id),
        "attendee_name": "X",
    })
    assert resp.status_code == 404


def test_join_waitlist_unknown_ticket_type(client, sold_out_event):
    resp = client.post(f"{WL_URL}/events/{sold_out_event.slug}/waitlist", json={
        "ticket_type_id": "00000000-0000-0000-0000-000000000000",
        "attendee_name": "X",
    })
    assert resp.status_code == 404


def test_join_waitlist_no_email(client, sold_out_event, sold_out_ticket_type, sold_out_order):
    resp = client.post(f"{WL_URL}/events/{sold_out_event.slug}/waitlist", json={
        "ticket_type_id": str(sold_out_ticket_type.id),
        "attendee_name": "Alice",
    })
    assert resp.status_code == 201


# --- Public: Leave Waitlist ---


def test_leave_waitlist_success(client, sold_out_event, sold_out_ticket_type, sold_out_order):
    join_resp = client.post(f"{WL_URL}/events/{sold_out_event.slug}/waitlist", json={
        "ticket_type_id": str(sold_out_ticket_type.id),
        "attendee_name": "Alice",
        "attendee_email": "alice@test.com",
    })
    entry_id = join_resp.get_json()["data"]["id"]
    link_code = join_resp.get_json()["data"]["attendee"]["link_code"]

    resp = client.delete(f"{WL_URL}/waitlist/{entry_id}", json={"link_code": link_code})
    assert resp.status_code == 204


def test_leave_waitlist_wrong_link_code(client, sold_out_event, sold_out_ticket_type, sold_out_order):
    join_resp = client.post(f"{WL_URL}/events/{sold_out_event.slug}/waitlist", json={
        "ticket_type_id": str(sold_out_ticket_type.id),
        "attendee_name": "Alice",
    })
    entry_id = join_resp.get_json()["data"]["id"]

    resp = client.delete(f"{WL_URL}/waitlist/{entry_id}", json={"link_code": "wrong"})
    assert resp.status_code == 409


def test_leave_waitlist_not_found(client):
    resp = client.delete(f"{WL_URL}/waitlist/{uuid.uuid4()}", json={"link_code": "x"})
    assert resp.status_code == 404


# --- Public: Check Position ---


def test_get_position_success(client, sold_out_event, sold_out_ticket_type, sold_out_order):
    client.post(f"{WL_URL}/events/{sold_out_event.slug}/waitlist", json={
        "ticket_type_id": str(sold_out_ticket_type.id),
        "attendee_name": "Alice",
        "attendee_email": "alice@test.com",
    })
    resp = client.get(f"{WL_URL}/events/{sold_out_event.slug}/waitlist/position?email=alice@test.com")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["position"] == 1


def test_get_position_not_found(client, sold_out_event):
    resp = client.get(f"{WL_URL}/events/{sold_out_event.slug}/waitlist/position?email=nobody@test.com")
    assert resp.status_code == 404


# --- Org: List Waitlist ---


def test_org_list_waitlist(client, admin_token, sold_out_event, sold_out_ticket_type, sold_out_order):
    client.post(f"{WL_URL}/events/{sold_out_event.slug}/waitlist", json={
        "ticket_type_id": str(sold_out_ticket_type.id),
        "attendee_name": "Alice",
        "attendee_email": "alice@test.com",
    })
    resp = client.get(
        f"{WL_URL}/org/events/{sold_out_event.id}/waitlist",
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data) == 1
    assert data[0]["attendee_email"] == "alice@test.com"


def test_org_list_waitlist_empty(client, admin_token, sold_out_event):
    resp = client.get(
        f"{WL_URL}/org/events/{sold_out_event.id}/waitlist",
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"] == []


def test_org_list_waitlist_not_found(client, admin_token):
    resp = client.get(
        f"{WL_URL}/org/events/{uuid.uuid4()}/waitlist",
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 404


# --- Org: Claim Entry ---


def test_claim_entry_success(client, db, admin_token, sold_out_event, sold_out_ticket_type, sold_out_order):
    join_resp = client.post(f"{WL_URL}/events/{sold_out_event.slug}/waitlist", json={
        "ticket_type_id": str(sold_out_ticket_type.id),
        "attendee_name": "Alice",
        "attendee_email": "alice@test.com",
    })
    entry_id = join_resp.get_json()["data"]["id"]

    resp = client.post(
        f"{WL_URL}/org/events/{sold_out_event.id}/waitlist/{entry_id}/claim",
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["claimed_at"] is not None
    assert data["expires_at"] is not None
    assert data["attendee"]["email"] == "alice@test.com"


def test_claim_entry_already_claimed(client, db, admin_token, sold_out_event, sold_out_ticket_type, sold_out_order):
    join_resp = client.post(f"{WL_URL}/events/{sold_out_event.slug}/waitlist", json={
        "ticket_type_id": str(sold_out_ticket_type.id),
        "attendee_name": "Alice",
    })
    entry_id = join_resp.get_json()["data"]["id"]

    client.post(
        f"{WL_URL}/org/events/{sold_out_event.id}/waitlist/{entry_id}/claim",
        headers=_auth_header(admin_token),
    )
    resp = client.post(
        f"{WL_URL}/org/events/{sold_out_event.id}/waitlist/{entry_id}/claim",
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 409


def test_claim_entry_not_found(client, admin_token, sold_out_event):
    resp = client.post(
        f"{WL_URL}/org/events/{sold_out_event.id}/waitlist/{uuid.uuid4()}/claim",
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 404


def test_claim_entry_wrong_org(client, db, admin_token, sold_out_event, sold_out_ticket_type, sold_out_order):
    other_org = Organization(id=uuid.uuid4(), name="Other", slug="other-org")
    db.session.add(other_org)
    db.session.commit()

    other_event = Event(
        id=uuid.uuid4(), organization_id=other_org.id,
        title="Other Event", date=datetime(2026, 12, 1, 10, 0, tzinfo=timezone.utc),
        capacity=100, status=EventStatus.PUBLISHED, seating_type=SeatingType.GENERAL,
        slug="other-event",
    )
    db.session.add(other_event)
    db.session.commit()

    join_resp = client.post(f"{WL_URL}/events/{sold_out_event.slug}/waitlist", json={
        "ticket_type_id": str(sold_out_ticket_type.id),
        "attendee_name": "Alice",
    })
    entry_id = join_resp.get_json()["data"]["id"]

    resp = client.post(
        f"{WL_URL}/org/events/{other_event.id}/waitlist/{entry_id}/claim",
        headers=_auth_header(admin_token),
    )
    assert resp.status_code == 404


# --- RBAC ---


def test_operator_can_list_waitlist(client, operator_token, sold_out_event):
    resp = client.get(
        f"{WL_URL}/org/events/{sold_out_event.id}/waitlist",
        headers=_auth_header(operator_token),
    )
    assert resp.status_code == 200


def test_checkin_staff_cannot_list_waitlist(client, checkin_token, sold_out_event):
    resp = client.get(
        f"{WL_URL}/org/events/{sold_out_event.id}/waitlist",
        headers=_auth_header(checkin_token),
    )
    assert resp.status_code == 403


def test_operator_cannot_claim_waitlist(client, operator_token, sold_out_event):
    resp = client.post(
        f"{WL_URL}/org/events/{sold_out_event.id}/waitlist/{uuid.uuid4()}/claim",
        headers=_auth_header(operator_token),
    )
    assert resp.status_code == 403
