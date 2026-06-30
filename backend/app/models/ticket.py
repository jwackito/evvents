from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.attendee import Attendee
    from app.models.event import TicketType
    from app.models.order import Order


class Ticket(TimestampMixin, db.Model):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )
    ticket_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ticket_types.id"), nullable=False, index=True
    )
    attendee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attendees.id"), nullable=False, index=True
    )
    qr_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    seat: Mapped[str | None] = mapped_column(String(50), nullable=True)
    checked_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    telegram_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    order: Mapped[Order] = relationship("Order", back_populates="tickets", lazy="selectin")
    ticket_type: Mapped[TicketType] = relationship("TicketType", lazy="selectin")
    attendee: Mapped[Attendee] = relationship("Attendee", back_populates="tickets", lazy="selectin")
