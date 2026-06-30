from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone

import factory
from factory.alchemy import SQLAlchemyModelFactory

from app.extensions import db as _db
from app.models.attendee import Attendee
from app.models.event import Event, EventStatus, SeatingType, TicketType
from app.models.order import Order, OrderStatus
from app.models.organization import Organization
from app.models.ticket import Ticket
from app.models.user import User, UserRole
from app.services.auth_service import hash_password


class OrganizationFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Organization
        sqlalchemy_session = _db.session

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Organization {n}")
    slug = factory.Sequence(lambda n: f"org-{n}")
    settings = factory.LazyFunction(dict)


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = _db.session

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    password_hash = factory.LazyFunction(lambda: hash_password("password123"))
    name = factory.Sequence(lambda n: f"User {n}")
    role = UserRole.OPERATOR
    organization = None
    organization_id = factory.LazyAttribute(lambda o: o.organization.id if o.organization else None)


class EventFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Event
        sqlalchemy_session = _db.session

    id = factory.LazyFunction(uuid.uuid4)
    organization = factory.SubFactory(OrganizationFactory)
    organization_id = factory.LazyAttribute(lambda o: o.organization.id if o.organization else None)
    title = factory.Sequence(lambda n: f"Event {n}")
    description = factory.Sequence(lambda n: f"Description for event {n}")
    date = factory.LazyFunction(lambda: datetime(2026, 9, 15, 9, 0, tzinfo=timezone.utc))
    location = factory.Sequence(lambda n: f"Venue {n}")
    capacity = 500
    status = EventStatus.DRAFT
    seating_type = SeatingType.GENERAL
    slug = factory.Sequence(lambda n: f"event-{n}")


class TicketTypeFactory(SQLAlchemyModelFactory):
    class Meta:
        model = TicketType
        sqlalchemy_session = _db.session

    id = factory.LazyFunction(uuid.uuid4)
    event = factory.SubFactory(EventFactory)
    event_id = factory.LazyAttribute(lambda o: o.event.id if o.event else None)
    name = factory.Sequence(lambda n: f"Ticket Type {n}")
    description = factory.Sequence(lambda n: f"Description for {n}")
    price = 0
    capacity = 400
    max_per_order = 5


class OrderFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Order
        sqlalchemy_session = _db.session

    id = factory.LazyFunction(uuid.uuid4)
    event = factory.SubFactory(EventFactory)
    event_id = factory.LazyAttribute(lambda o: o.event.id if o.event else None)
    status = OrderStatus.PENDING


class AttendeeFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Attendee
        sqlalchemy_session = _db.session

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Attendee {n}")
    email = factory.Sequence(lambda n: f"attendee{n}@test.com")
    telegram_chat_id = None
    telegram_linked = False
    link_code = factory.LazyFunction(lambda: secrets.token_hex(8))


class TicketFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Ticket
        sqlalchemy_session = _db.session

    id = factory.LazyFunction(uuid.uuid4)
    order = factory.SubFactory(OrderFactory)
    order_id = factory.LazyAttribute(lambda o: o.order.id if o.order else None)
    ticket_type = factory.SubFactory(TicketTypeFactory)
    ticket_type_id = factory.LazyAttribute(lambda o: o.ticket_type.id if o.ticket_type else None)
    attendee = factory.SubFactory(AttendeeFactory)
    attendee_id = factory.LazyAttribute(lambda o: o.attendee.id if o.attendee else None)
    qr_hash = factory.LazyFunction(lambda: hashlib.sha256(
        f"{uuid.uuid4()}-{secrets.token_hex(16)}".encode()
    ).hexdigest())
    seat = None
    checked_in = False
    checked_in_at = None
    telegram_message_id = None
