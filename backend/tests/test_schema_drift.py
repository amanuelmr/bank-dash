"""The migrated schema must match what the models declare.

This exists because the two can drift apart silently, and did: adding a column
to a model left existing databases without it, because `create_all` creates
missing *tables* but never adds missing *columns*. Every login then failed with a
500 and no unit test complained - the suite builds its schema from the models, so
it agreed with itself.

The seeder has the same blind spot, which is why CI runs `alembic upgrade head`
rather than trusting `python -m app.seed` to produce the schema.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

# Importing every model module is what registers the tables on Base.metadata.
from app.models import bank_service, card, company, loan, transaction, user  # noqa: F401
from app.models.base import Base

BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _run_migrations(db_path: Path) -> None:
    """Run alembic against an empty SQLite file at *db_path*.

    Alembic's env.py takes its URL from app settings, which is async, so the
    subprocess gets the async form. A sync sqlite:// URL there fails with
    "the asyncio extension requires an async driver".
    """
    command = (
        "from alembic import command;"
        "from alembic.config import Config;"
        "cfg = Config('alembic.ini');"
        "cfg.set_main_option('script_location', 'alembic');"
        "command.upgrade(cfg, 'head')"
    )
    result = subprocess.run(
        [sys.executable, "-c", command],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{db_path}"},
    )
    assert result.returncode == 0, (
        f"alembic upgrade head failed:\n{result.stdout}\n{result.stderr}"
    )


@pytest.mark.parametrize("table", sorted(Base.metadata.tables))
def test_migration_produces_the_columns_the_model_declares(table, tmp_path):
    db_path = tmp_path / "drift.db"
    _run_migrations(db_path)

    engine = create_engine(f"sqlite:///{db_path}")
    try:
        migrated = {c["name"] for c in inspect(engine).get_columns(table)}
    finally:
        engine.dispose()

    assert migrated == {c.name for c in Base.metadata.tables[table].columns}, (
        f"{table}: the migration and the model disagree. A column added to the "
        f"model needs a new alembic revision, or existing databases fail at "
        f"runtime while the test suite - which builds from the models - stays green."
    )