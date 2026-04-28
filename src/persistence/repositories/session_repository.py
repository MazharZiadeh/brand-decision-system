"""Canonical repository pattern for the persistence layer.

Other repositories (questionnaire, pain, register, etc.) are added in the
sessions that build the services consuming them. This file is the working
example future repositories follow.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.session import Session
from src.persistence.converters import session_from_orm, session_to_orm
from src.persistence.models import Session as SessionORM


class SessionRepository:
    """Read/write Sessions via domain models. ORM details do not leak."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, session: Session) -> Session:
        orm = session_to_orm(session)
        self._db.add(orm)
        await self._db.flush()
        return session_from_orm(orm)

    async def get(self, session_id: uuid.UUID) -> Session | None:
        result = await self._db.execute(select(SessionORM).where(SessionORM.id == session_id))
        orm = result.scalar_one_or_none()
        return session_from_orm(orm) if orm is not None else None

    async def list_for_facilitator(self, facilitator_id: uuid.UUID) -> list[Session]:
        result = await self._db.execute(
            select(SessionORM)
            .where(SessionORM.facilitator_id == facilitator_id)
            .order_by(SessionORM.created_at.desc())
        )
        return [session_from_orm(orm) for orm in result.scalars().all()]

    async def update(self, session: Session) -> Session:
        """Update an existing session's mutable fields (currently `phase` and
        `updated_at`). Raises if the row does not exist.
        """
        result = await self._db.execute(select(SessionORM).where(SessionORM.id == session.id))
        orm = result.scalar_one()
        orm.phase = session.phase.value
        orm.updated_at = session.updated_at
        await self._db.flush()
        return session_from_orm(orm)
