"""Persist and retrieve LLM call audit records.

Per CLAUDE.md §2.8 every LLM call must be audited. This repository is the
persistence side of that invariant. The orchestration code that calls the
LLM provider receives an `LLMCallRecord` on every call (success or
failure) and writes it via this repository — typically inside the same
transaction that persists the resulting `ModuleOutput` or `PainAnalysis`.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.audit import LLMCallRecord
from src.persistence.converters import llm_call_record_from_orm, llm_call_record_to_orm
from src.persistence.models import LLMCallRecord as LLMCallRecordORM


class LLMCallRecordRepository:
    """Domain-typed read/write of LLM call audit records."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, record: LLMCallRecord) -> LLMCallRecord:
        orm = llm_call_record_to_orm(record)
        self._db.add(orm)
        await self._db.flush()
        return llm_call_record_from_orm(orm)

    async def get(self, record_id: uuid.UUID) -> LLMCallRecord | None:
        result = await self._db.execute(
            select(LLMCallRecordORM).where(LLMCallRecordORM.id == record_id)
        )
        orm = result.scalar_one_or_none()
        return llm_call_record_from_orm(orm) if orm is not None else None

    async def list_for_session(self, session_id: uuid.UUID) -> list[LLMCallRecord]:
        result = await self._db.execute(
            select(LLMCallRecordORM)
            .where(LLMCallRecordORM.session_id == session_id)
            .order_by(LLMCallRecordORM.called_at.asc())
        )
        return [llm_call_record_from_orm(orm) for orm in result.scalars().all()]
