"""Shared rollback-only Postgres fixture for explicitly enabled integration tests."""

import os
from uuid import uuid4

import pytest
from psycopg.conninfo import conninfo_to_dict

from caseflow.config import Settings
from caseflow.database import KnowledgeStore, connect, migrate


@pytest.fixture
def db():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a local test database to run integration tests")
    info = conninfo_to_dict(url)
    if (
        info.get("host") not in {"127.0.0.1", "localhost", "::1"}
        or info.get("dbname") != "copilot_test"
    ):
        pytest.fail("Integration tests require a loopback-only database named copilot_test")
    settings = Settings(database_url=url)
    migrate(settings)
    with connect(settings) as conn:
        prefix = "test-" + uuid4().hex
        tenants = (prefix + "-a", prefix + "-b")
        for tenant in tenants:
            conn.execute("INSERT INTO tenants (id, name) VALUES (%s, %s)", (tenant, tenant))
        try:
            yield KnowledgeStore(conn, "test-model"), tenants
        finally:
            conn.rollback()
