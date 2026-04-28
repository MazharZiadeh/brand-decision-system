"""Migration integrity test: upgrade → downgrade → upgrade against real Postgres.

These tests require a running Postgres matching the configured `DATABASE_URL`.
They are marked `integration` and excluded from the default pytest run.
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from src.config import get_settings

pytestmark = pytest.mark.integration


EXPECTED_TABLES = {
    "alembic_version",
    "answer",
    "answer_option",
    "decision_scope",
    "execution_plan",
    "export_artifact",
    "facilitator",
    "language_register",
    "llm_call_record",
    "module_output",
    "pain_analysis",
    "pain_category",
    "pain_taxonomy",
    "question",
    "questionnaire_instance",
    "questionnaire_version",
    "rationale",
    "rule",
    "session",
    "session_system_prompt",
}


def _alembic_config() -> Config:
    return Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))


def _async_url() -> str:
    url = get_settings().database_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def _list_tables() -> set[str]:
    eng = create_async_engine(_async_url(), pool_pre_ping=True)
    try:
        async with eng.connect() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: set(inspect(sync_conn).get_table_names())
            )
        return tables
    finally:
        await eng.dispose()


def test_upgrade_to_head_succeeds():
    cfg = _alembic_config()
    command.upgrade(cfg, "head")


async def test_all_expected_tables_present_after_upgrade():
    tables = await _list_tables()
    missing = EXPECTED_TABLES - tables
    assert not missing, f"Missing tables after upgrade: {missing}"


def test_downgrade_to_base_then_upgrade_to_head_cycle():
    cfg = _alembic_config()
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


async def test_session_table_has_expected_indexes():
    """Spot-check: session.facilitator_id and session.questionnaire_version_id
    must be indexed (every FK column gets an index per the convention)."""
    eng = create_async_engine(_async_url(), pool_pre_ping=True)
    try:
        async with eng.connect() as conn:
            indexes = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_indexes("session")
            )
        indexed_columns: set[str] = set()
        for idx in indexes:
            indexed_columns.update(idx["column_names"])
        assert "facilitator_id" in indexed_columns
        assert "questionnaire_version_id" in indexed_columns
    finally:
        await eng.dispose()
