"""LLMCallRecordRepository CRUD round-trip against live Postgres.

Marked `integration` and excluded from the default pytest run. Each test
runs inside the function-scoped transactional fixture from
`tests/integration/conftest.py`.
"""

import asyncio
import uuid
from datetime import UTC, datetime

import pytest

from src.domain.audit import LLMCallRecord, LLMCallStatus
from src.domain.facilitator import Facilitator
from src.domain.language import Language
from src.domain.questionnaire import QuestionnaireVersion
from src.domain.session import Session
from src.persistence.converters import (
    facilitator_to_orm,
    questionnaire_version_to_orm,
    session_to_orm,
)
from src.persistence.repositories import LLMCallRecordRepository

pytestmark = pytest.mark.integration


async def _seed_session(db_session) -> uuid.UUID:
    """Insert a Facilitator + QuestionnaireVersion + Session and return the
    session id. The LLMCallRecord.session_id FK requires an existing session.
    """
    f = Facilitator(email=f"f-{uuid.uuid4()}@example.com", display_name="Tester")
    qv = QuestionnaireVersion(version="1.0.0", content_hash="x" * 8, questions=[])
    s = Session(facilitator_id=f.id, questionnaire_version_id=qv.id)
    db_session.add(facilitator_to_orm(f))
    db_session.add(questionnaire_version_to_orm(qv))
    db_session.add(session_to_orm(s))
    await db_session.flush()
    return s.id


def _record(session_id: uuid.UUID, *, called_at: datetime | None = None) -> LLMCallRecord:
    return LLMCallRecord(
        session_id=session_id,
        prompt_hash="a" * 16,
        model_version="mock-fixed-v1",
        language_directive=Language.ENGLISH,
        parameters={"temperature": 0.7, "max_tokens": 2000},
        response_text='{"theme":"…"}',
        latency_ms=120,
        status=LLMCallStatus.SUCCESS,
        called_at=called_at or datetime.now(UTC),
    )


async def test_create_and_get_round_trips_all_fields(db_session):
    sid = await _seed_session(db_session)
    repo = LLMCallRecordRepository(db_session)

    domain = _record(sid)
    created = await repo.create(domain)
    assert created.id == domain.id

    fetched = await repo.get(domain.id)
    assert fetched is not None
    assert fetched.session_id == sid
    assert fetched.model_version == "mock-fixed-v1"
    assert fetched.language_directive == Language.ENGLISH
    assert fetched.status == LLMCallStatus.SUCCESS
    assert fetched.parameters == {"temperature": 0.7, "max_tokens": 2000}
    assert fetched.latency_ms == 120


async def test_get_returns_none_for_missing_record(db_session):
    repo = LLMCallRecordRepository(db_session)
    assert await repo.get(uuid.uuid4()) is None


async def test_list_for_session_returns_records_in_chronological_order(db_session):
    sid = await _seed_session(db_session)
    repo = LLMCallRecordRepository(db_session)

    t0 = datetime.now(UTC)
    # Three records with strictly increasing timestamps.
    r1 = await repo.create(_record(sid, called_at=t0))
    await asyncio.sleep(0.01)
    r2 = await repo.create(_record(sid, called_at=datetime.now(UTC)))
    await asyncio.sleep(0.01)
    r3 = await repo.create(_record(sid, called_at=datetime.now(UTC)))

    listed = await repo.list_for_session(sid)
    listed_ids = [r.id for r in listed]
    assert listed_ids == [r1.id, r2.id, r3.id]


async def test_list_for_session_with_no_records_returns_empty_list(db_session):
    sid = await _seed_session(db_session)
    repo = LLMCallRecordRepository(db_session)
    assert await repo.list_for_session(sid) == []
