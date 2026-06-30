from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.user import User


class Organization(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    telegram_bot_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    users: Mapped[list[User]] = relationship("User", back_populates="organization", lazy="selectin")
    events: Mapped[list[Event]] = relationship(
        "Event", back_populates="organization", lazy="selectin"
    )
