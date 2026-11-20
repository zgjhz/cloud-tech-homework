"""Optionally initialize only the disposable CI database before API tests."""

import os
import time
from pathlib import Path

import psycopg
import pytest

from app.main import connect


@pytest.fixture(scope="session", autouse=True)
def prepare_ci_database():
    if os.environ.get("INIT_TEST_DATABASE") != "1":
        return
    if os.environ.get("PGDATABASE") != "homework_ci":
        raise RuntimeError("Initialization is restricted to homework_ci")
    for attempt in range(30):
        try:
            with connect() as conn:
                if conn.execute("SELECT to_regclass('public.items') AS name").fetchone()["name"] is None:
                    conn.execute((Path(__file__).resolve().parents[1] / "db/init.sql").read_text())
            return
        except psycopg.OperationalError:
            if attempt == 29:
                raise
            time.sleep(1)
