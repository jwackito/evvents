from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.organization import Organization
    from app.models.waitlist import WaitlistEntry


class EventStatus(str, PyEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class SeatingType(str, PyEnum):
    GENERAL = "general"
    ASSIGNED = "assigned"


class Event(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=EventStatus.DRAFT,
    )
    seating_type: Mapped[SeatingType] = mapped_column(
        Enum(SeatingType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=SeatingType.GENERAL,
    )
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cover_image: Mapped[str | None] = mapped_column(String(512), nullable=True)

    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="events", lazy="selectin"
    )
    ticket_types: Mapped[list[TicketType]] = relationship(
        "TicketType", back_populates="event", lazy="selectin", cascade="all, delete-orphan"
    )
    orders: Mapped[list[Order]] = relationship(
        "Order", back_populates="event", lazy="dynamic"
    )
    waitlist_entries: Mapped[list[WaitlistEntry]] = relationship(
        "WaitlistEntry", back_populates="event", lazy="dynamic"
    )

    __table_args__ = (
        db.UniqueConstraint("organization_id", "slug", name="uq_event_org_slug"),
    )


class TicketType(TimestampMixin, db.Model):
    __tablename__ = "ticket_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    max_per_order: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    event: Mapped[Event] = relationship("Event", back_populates="ticket_types", lazy="selectin")
