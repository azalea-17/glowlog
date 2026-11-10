"""Integration tests. Need a running PostgreSQL + Redis (e.g. `docker compose up -d db redis`
with DB_HOST/REDIS_HOST=localhost). Run:  GLOWLOG_SKIP_INIT=1 pytest -q"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("GLOWLOG_SKIP_INIT", "1")

import app as glow  # noqa: E402


@pytest.fixture()
def client():
    flask_app = glow.create_app()
    conn = glow.get_db()
    with conn, conn.cursor() as cur:
        cur.execute("TRUNCATE routines RESTART IDENTITY")
    conn.close()
    glow.get_cache().delete(glow.CACHE_KEY)
    return flask_app.test_client()


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "healthy"


def test_index_page(client):
    assert client.get("/").status_code == 200


def test_create_returns_201_and_location(client):
    r = client.post("/api/routines", json={"title": "Weekday glow", "period": "morning",
                                           "products": "Cleanser, SPF"})
    assert r.status_code == 201
    assert r.headers["Location"] == f"/api/routines/{r.get_json()['id']}"
    assert r.get_json()["period"] == "morning"


@pytest.mark.parametrize("payload", [
    {}, {"title": "", "period": "morning"}, {"title": "x", "period": "noon"},
    {"title": "x" * 101, "period": "night"},
])
def test_create_validation_400(client, payload):
    assert client.post("/api/routines", json=payload).status_code == 400


def test_create_non_json_400(client):
    assert client.post("/api/routines", data="nope").status_code == 400


def test_list_and_cache_hit_then_invalidate(client):
    client.post("/api/routines", json={"title": "A", "period": "morning"})
    first = client.get("/api/routines")
    second = client.get("/api/routines")
    assert first.status_code == 200 and first.headers["X-Cache"] == "MISS"
    assert second.headers["X-Cache"] == "HIT"
    client.post("/api/routines", json={"title": "B", "period": "night"})
    third = client.get("/api/routines")
    assert third.headers["X-Cache"] == "MISS"  # POST invalidated the cache
    assert [r["title"] for r in third.get_json()] == ["B", "A"]


def test_filter_by_period(client):
    client.post("/api/routines", json={"title": "A", "period": "morning"})
    client.post("/api/routines", json={"title": "B", "period": "night"})
    r = client.get("/api/routines?period=night")
    assert [x["title"] for x in r.get_json()] == ["B"]
    assert client.get("/api/routines?period=bad").status_code == 400
