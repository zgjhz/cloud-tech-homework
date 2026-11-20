"""HTTP entry point for the persistent PostgreSQL lab."""

import asyncio
import os
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row
from pydantic import BaseModel, ConfigDict, Field


def connect():
    return psycopg.connect(
        host=os.environ.get("PGHOST", "db"),
        port=os.environ.get("PGPORT", "5432"),
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        connect_timeout=3,
        row_factory=dict_row,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Compose waits for health; bounded retries also support standalone startup.
    for attempt in range(10):
        try:
            with connect() as conn:
                conn.execute("SELECT 1 FROM items LIMIT 1")
            break
        except psycopg.OperationalError:
            if attempt == 9:
                raise
            await asyncio.sleep(1)
    yield


app = FastAPI(title="Homework 02 — persistent items", lifespan=lifespan)


class ItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=200)


class Item(ItemInput):
    id: int


@app.exception_handler(psycopg.OperationalError)
async def database_unavailable(request, exc):
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


@app.get("/health")
def health():
    with connect() as conn:
        conn.execute("SELECT 1 FROM items LIMIT 1")
    return {"status": "ok"}


@app.post("/items", response_model=Item, status_code=201)
def create_item(item: ItemInput):
    with connect() as conn:
        return conn.execute(
            "INSERT INTO items (name) VALUES (%s) RETURNING id, name", (item.name,)
        ).fetchone()


@app.get("/items", response_model=list[Item])
def list_items():
    with connect() as conn:
        return conn.execute("SELECT id, name FROM items ORDER BY id").fetchall()
