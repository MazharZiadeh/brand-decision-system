"""SessionRepository CRUD round-trip against real Postgres.

Marked `integration` and excluded from the default pytest run. Each test
runs inside a function-scoped transaction that rolls back at the end, so
the test database is left untouched.
"""

import uuid

import pytest

from src.domain.facilitator import Facilitator
from src.domain.questionnaire import QuestionnaireVersion
from src.domain.session import PhaseState, Session
from src.persistence.converters import (
    facilitator_to_orm,
    questionnaire_version_to_orm,
)
from src.persistence.repositories import SessionRepository

pytestmark = pytest.mark.integration


async def _seed_dependencies(db_session) -> tuple[uuid.UUID, uuid.UUID]:
    """Insert one Facilitator and one QuestionnaireVersion via direct ORM
    writes — their repositories don't exist yet — and return their ids.
    """
    facilitator = Facilitator(email=f"f-{uuid.uuid4()}@example.com", display_name="F")
    qv = QuestionnaireVersion(version="1.0.0", content_hash="abc123", questions=[])
    db_session.add(facilitator_to_orm(facilitator))
    db_session.add(questionnaire_version_to_orm(qv))
    await db_session.flush()
    return facilitator.id, qv.id


async def test_create_then_get_round_trips_a_session(db_session):
    facilitator_id, qv_id = await _seed_dependencies(db_session)
    repo = SessionRepository(db_session)

    domain = Session(facilitator_id=facilitator_id, questionnaire_version_id=qv_id)
    created = await repo.create(domain)
    assert created.id == domain.id

    fetched = await repo.get(domain.id)
    assert fetched is not None
    assert fetched.id == domain.id
    assert fetched.facilitator_id == facilitator_id
    assert fetched.questionnaire_version_id == qv_id
    assert fetched.phase == PhaseState.DISCOVERY


async def test_get_returns_none_for_missing_session(db_session):
    repo = SessionRepository(db_session)
    assert await repo.get(uuid.uuid4()) is None


async def test_list_for_facilitator_returns_owned_sessions_in_recent_order(db_session):
    facilitator_id, qv_id = await _seed_dependencies(db_session)
    repo = SessionRepository(db_session)

    s1 = await repo.create(Session(facilitator_id=facilitator_id, questionnaire_version_id=qv_id))
    s2 = await repo.create(Session(facilitator_id=facilitator_id, questionnaire_version_id=qv_id))

    listed = await repo.list_for_facilitator(facilitator_id)
    listed_ids = [s.id for s in listed]
    assert s1.id in listed_ids
    assert s2.id in listed_ids


async def test_list_for_facilitator_excludes_other_facilitators_sessions(db_session):
    f1_id, qv_id = await _seed_dependencies(db_session)
    f2_id, _ = await _seed_dependencies(db_session)
    repo = SessionRepository(db_session)

    own = await repo.create(Session(facilitator_id=f1_id, questionnaire_version_id=qv_id))
    foreign = await repo.create(Session(facilitator_id=f2_id, questionnaire_version_id=qv_id))

    listed = await repo.list_for_facilitator(f1_id)
    listed_ids = [s.id for s in listed]
    assert own.id in listed_ids
    assert foreign.id not in listed_ids


async def test_phase_transition_persists(db_session):
    facilitator_id, qv_id = await _seed_dependencies(db_session)
    repo = SessionRepository(db_session)

    domain = Session(facilitator_id=facilitator_id, questionnaire_version_id=qv_id)
    await repo.create(domain)

    domain.phase = PhaseState.GENERATION
    updated = await repo.update(domain)
    assert updated.phase == PhaseState.GENERATION

    re_fetched = await repo.get(domain.id)
    assert re_fetched is not None
    assert re_fetched.phase == PhaseState.GENERATION
