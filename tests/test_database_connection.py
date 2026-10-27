"""Exercise transaction timeouts with a pooler-like startup restriction."""

import os

import psycopg
import pytest

from caseflow.config import Settings
from caseflow.database import connect


@pytest.mark.integration
def test_pooler_compatible_connection_still_enforces_query_timeout(db, monkeypatch):
    # The db fixture has already verified this is the separate loopback test DB.
    # Connection.info.dsn intentionally omits its password, so use the test setting.
    settings = Settings(database_url=os.environ["TEST_DATABASE_URL"])
    original_connect = psycopg.connect

    def pooled_connect(*args, **kwargs):
        if "options" in kwargs:
            raise psycopg.OperationalError("unsupported startup parameter: statement_timeout")
        return original_connect(*args, **kwargs)

    monkeypatch.setattr(psycopg, "connect", pooled_connect)
    with connect(settings) as conn:
        assert conn.execute("SHOW statement_timeout").fetchone()["statement_timeout"] == "10s"
        with pytest.raises(psycopg.errors.QueryCanceled), conn.transaction():
            conn.execute("SET LOCAL statement_timeout = '20ms'")
            conn.execute("SELECT pg_sleep(0.2)")
        # Rolling back the failed savepoint restores the surrounding transaction's
        # timeout, and the same connection remains usable.
        assert conn.execute("SHOW statement_timeout").fetchone()["statement_timeout"] == "10s"
        assert conn.execute("SELECT 1 AS n").fetchone()["n"] == 1
