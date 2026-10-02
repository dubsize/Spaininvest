"""Test configuration.

Tests run against SQLite by default (fast, no services needed). Set
TEST_DATABASE_URL=postgresql+psycopg://... to run the DB/API tests against PostgreSQL.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp(prefix="arbscan-test-")
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{_tmp}/test.db")
os.environ["REDIS_URL"] = "redis://127.0.0.1:1/0"  # unreachable on purpose -> in-process fallbacks
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "test-password"
os.environ["ADMIN_PASSWORD_HASH"] = ""
os.environ["JWT_SECRET"] = "test-secret-with-at-least-32-bytes-of-entropy"
os.environ["LOG_JSON"] = "false"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["SMTP_HOST"] = ""
os.environ["EBAY_CLIENT_ID"] = ""
os.environ["EBAY_CLIENT_SECRET"] = ""
os.environ["API_RATE_LIMIT_PER_MINUTE"] = "100000"
os.environ["LOGIN_RATE_LIMIT_PER_MINUTE"] = "100000"

import pytest  # noqa: E402

from arbscan.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from arbscan.db.models import Base  # noqa: E402
from arbscan.db.session import SessionLocal, get_engine  # noqa: E402
from arbscan.normalization.catalog import entries_from_seed, normalizer_cache  # noqa: E402
from arbscan.normalization.engine import RuleNormalizer  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def normalizer() -> RuleNormalizer:
    return RuleNormalizer(entries_from_seed())


@pytest.fixture(scope="session")
def seeded_db():
    """Schema + reference data + demo data, created once per test session."""
    from arbscan.seed.loader import seed_demo_data, seed_reference_data

    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    normalizer_cache.invalidate()
    s = SessionLocal()
    seed_reference_data(s)
    s.commit()
    seed_demo_data(s)
    s.commit()
    s.close()
    yield engine


@pytest.fixture
def db(seeded_db):
    s = SessionLocal()
    try:
        yield s
    finally:
        s.rollback()
        s.close()


@pytest.fixture
def client(seeded_db):
    from fastapi.testclient import TestClient

    from arbscan.api.main import create_app

    with TestClient(create_app()) as c:
        r = c.post("/api/auth/login", json={"username": "admin", "password": "test-password"})
        assert r.status_code == 200, r.text
        c.headers["X-CSRF-Token"] = r.json()["csrf_token"]
        yield c


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")
