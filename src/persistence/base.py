from datetime import UTC, datetime

from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for every ORM model in src/persistence/models.py."""


class TimestampMixin:
    """Mixin providing a timezone-aware `created_at` column.

    Models that also need `updated_at` declare it on the model itself rather
    than via a second mixin, since updated_at semantics (touch on every UPDATE)
    are SQLAlchemy event-driven, not column-default driven.
    """

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
