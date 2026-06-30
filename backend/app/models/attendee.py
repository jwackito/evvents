from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.ticket import Ticket


class Attendee(TimestampMixin, db.Model):
    __tablename__ = "attendees"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    telegram_linked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    link_code: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)

    tickets: Mapped[list[Ticket]] = relationship(
        "Ticket", back_populates="attendee", lazy="selectin"
    )
