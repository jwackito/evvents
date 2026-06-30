from __future__ import annotations

import uuid
from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.extensions import db as _db
from app.models.attendee import Attendee
from app.models.event import Event, EventStatus, SeatingType, TicketType
from app.models.order import Order, OrderStatus
from app.models.organization import Organization
from app.models.ticket import Ticket
from app.models.user import User, UserRole
from app.services.auth_service import hash_password
from app.utils.jwt import create_access_token


@pytest.fixture
def app() -> Generator[Flask, None, None]:
    application = create_app()
    application.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "postgresql://evvents:evvents@db:5432/evvents",
    })
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def db(app: Flask):
    return _db


@pytest.fixture
def org(db) -> Organization:
    org = Organization(
        id=uuid.uuid4(),
        name="Test Organization",
        slug="test-org",
        settings={},
    )
    db.session.add(org)
    db.session.commit()
    return org


@pytest.fixture
def admin_user(db, org: Organization) -> User:
    user = User(
        id=uuid.uuid4(),
        email="admin@test.com",
        password_hash=hash_password("password123"),
        name="Admin User",
        role=UserRole.ADMIN,
        organization_id=org.id,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def operator_user(db, org: Organization) -> User:
    user = User(
        id=uuid.uuid4(),
        email="operator@test.com",
        password_hash=hash_password("password123"),
        name="Operator User",
        role=UserRole.OPERATOR,
        organization_id=org.id,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def checkin_user(db, org: Organization) -> User:
    user = User(
        id=uuid.uuid4(),
        email="checkin@test.com",
        password_hash=hash_password("password123"),
        name="Check-in Staff",
        role=UserRole.CHECKIN_STAFF,
        organization_id=org.id,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def no_org_user(db) -> User:
    user = User(
        id=uuid.uuid4(),
        email="nobody@test.com",
        password_hash=hash_password("password123"),
        name="No Org User",
        role=UserRole.OPERATOR,
        organization_id=None,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token(admin_user.id, {"role": admin_user.role.value})


@pytest.fixture
def super_admin_user(db) -> User:
    user = User(
        id=uuid.uuid4(),
        email="super@admin.com",
        password_hash=hash_password("password123"),
        name="Super Admin",
        role=UserRole.ADMIN,
        organization_id=None,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def super_admin_token(super_admin_user: User) -> str:
    return create_access_token(super_admin_user.id, {"role": super_admin_user.role.value})


@pytest.fixture
def operator_token(operator_user: User) -> str:
    return create_access_token(operator_user.id, {"role": operator_user.role.value})


@pytest.fixture
def checkin_token(checkin_user: User) -> str:
    return create_access_token(checkin_user.id, {"role": checkin_user.role.value})


@pytest.fixture
def no_org_token(no_org_user: User) -> str:
    return create_access_token(no_org_user.id, {"role": no_org_user.role.value})


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def published_event(db, org: Organization) -> Event:
    event = Event(
        id=uuid.uuid4(),
        organization_id=org.id,
        title="Python Conference",
        description="Annual Python conference",
        date=datetime(2026, 9, 15, 9, 0, tzinfo=timezone.utc),
        location="Convention Center",
        capacity=500,
        status=EventStatus.PUBLISHED,
        seating_type=SeatingType.GENERAL,
        slug="python-conf-2026",
    )
    db.session.add(event)
    db.session.commit()
    return event


@pytest.fixture
def draft_event(db, org: Organization) -> Event:
    event = Event(
        id=uuid.uuid4(),
        organization_id=org.id,
        title="Draft Event",
        description="Not published yet",
        date=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
        location="TBD",
        capacity=100,
        status=EventStatus.DRAFT,
        seating_type=SeatingType.GENERAL,
        slug="draft-event",
    )
    db.session.add(event)
    db.session.commit()
    return event


@pytest.fixture
def ticket_type(db, published_event: Event) -> TicketType:
    tt = TicketType(
        id=uuid.uuid4(),
        event_id=published_event.id,
        name="General Admission",
        description="Standard entry",
        price=0,
        capacity=400,
        max_per_order=5,
    )
    db.session.add(tt)
    db.session.commit()
    return tt


@pytest.fixture
def vip_ticket_type(db, published_event: Event) -> TicketType:
    tt = TicketType(
        id=uuid.uuid4(),
        event_id=published_event.id,
        name="VIP",
        description="Premium entry",
        price=0,
        capacity=100,
        max_per_order=2,
    )
    db.session.add(tt)
    db.session.commit()
    return tt


@pytest.fixture
def created_order(db, published_event: Event, ticket_type: TicketType) -> tuple[Order, Attendee, Ticket]:
    attendee = Attendee(
        id=uuid.uuid4(),
        name="John Doe",
        email="john@test.com",
        link_code="test-link-code",
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
        qr_hash="a" * 64,
    )
    db.session.add(ticket)
    db.session.commit()

    return order, attendee, ticket
