"""Integration tests: run against the lab DB; remove only records we create."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app, connect


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_read_from_database(client):
    name = f"test-{uuid4()} O'Reilly"
    item_id = None
    try:
        response = client.post("/items", json={"name": name})
        assert response.status_code == 201
        item = response.json()
        item_id = item["id"]
        assert isinstance(item_id, int)
        assert item["name"] == name
        assert item in client.get("/items").json()
        with connect() as conn:
            assert conn.execute(
                "SELECT name FROM items WHERE id = %s", (item_id,)
            ).fetchone()["name"] == name
    finally:
        if item_id is not None:
            with connect() as conn:
                conn.execute("DELETE FROM items WHERE id = %s", (item_id,))


@pytest.mark.parametrize("payload", [{}, {"name": ""}, {"name": "   "},
                                   {"name": "x" * 201}, {"name": 42},
                                   {"name": "valid", "unexpected": True}])
def test_invalid_input(client, payload):
    assert client.post("/items", json=payload).status_code == 422
