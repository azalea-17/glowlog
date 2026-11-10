"""GlowLog - Skincare Routine Tracker (Flask + PostgreSQL + Redis cache)."""
import json
import os
import time

import psycopg2
import psycopg2.extras
import redis
from flask import Flask, jsonify, render_template, request

VALID_PERIODS = ("morning", "night")
CACHE_KEY = "glowlog:routines"


def env(name, default=None):
    return os.environ.get(name, default)


def get_db():
    """Open a new PostgreSQL connection. Host is the Compose service name."""
    return psycopg2.connect(
        host=env("DB_HOST", "db"),
        port=int(env("DB_PORT", "5432")),
        user=env("POSTGRES_USER", "glowlog"),
        password=env("POSTGRES_PASSWORD", ""),
        dbname=env("POSTGRES_DB", "glowlog"),
        connect_timeout=3,
    )


def get_cache():
    return redis.Redis(
        host=env("REDIS_HOST", "redis"),
        port=int(env("REDIS_PORT", "6379")),
        socket_connect_timeout=1,
        socket_timeout=1,
        decode_responses=True,
    )


def init_schema(retries=15, delay=2):
    """Create the table if missing. Retries so the app survives a slow DB start."""
    for attempt in range(1, retries + 1):
        try:
            conn = get_db()
            with conn, conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS routines (
                        id          SERIAL PRIMARY KEY,
                        title       VARCHAR(100) NOT NULL,
                        period      VARCHAR(10)  NOT NULL CHECK (period IN ('morning','night')),
                        products    TEXT         NOT NULL DEFAULT '',
                        notes       TEXT         NOT NULL DEFAULT '',
                        created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
                    )
                    """
                )
            conn.close()
            return
        except psycopg2.OperationalError:
            if attempt == retries:
                raise
            time.sleep(delay)


def row_to_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "period": row["period"],
        "products": row["products"],
        "notes": row["notes"],
        "created_at": row["created_at"].isoformat(),
    }


def create_app(run_init=True):
    app = Flask(__name__)
    if run_init:
        init_schema()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        """Liveness + dependency check. 200 if all good, 503 otherwise."""
        status = {"app": "ok", "database": "ok", "cache": "ok"}
        try:
            conn = get_db()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            conn.close()
        except Exception:
            status["database"] = "down"
        try:
            get_cache().ping()
        except Exception:
            status["cache"] = "down"
        healthy = status["database"] == "ok" and status["cache"] == "ok"
        status["status"] = "healthy" if healthy else "unhealthy"
        return jsonify(status), (200 if healthy else 503)

    @app.get("/api/routines")
    def list_routines():
        """Read endpoint. Redis cache-aside: HIT returns cached JSON, MISS reads DB."""
        period = request.args.get("period")
        if period is not None and period not in VALID_PERIODS:
            return jsonify(error="period must be 'morning' or 'night'"), 400

        cache = get_cache()
        cache_state = "MISS"
        data = None
        try:
            cached = cache.get(CACHE_KEY)
            if cached:
                data = json.loads(cached)
                cache_state = "HIT"
        except redis.RedisError:
            cache_state = "BYPASS"  # Redis down -> still serve from the DB

        if data is None:
            conn = get_db()
            with conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM routines ORDER BY created_at DESC, id DESC")
                data = [row_to_dict(r) for r in cur.fetchall()]
            conn.close()
            try:
                cache.set(CACHE_KEY, json.dumps(data), ex=int(env("CACHE_TTL_SECONDS", "30")))
            except redis.RedisError:
                pass

        if period:
            data = [r for r in data if r["period"] == period]
        resp = jsonify(data)
        resp.headers["X-Cache"] = cache_state
        return resp, 200

    @app.post("/api/routines")
    def create_routine():
        """Write endpoint. 201 Created on success, 400 on invalid input."""
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(error="request body must be JSON"), 400

        title = str(body.get("title", "")).strip()
        period = str(body.get("period", "")).strip().lower()
        products = str(body.get("products", "")).strip()
        notes = str(body.get("notes", "")).strip()

        errors = {}
        if not title or len(title) > 100:
            errors["title"] = "required, max 100 characters"
        if period not in VALID_PERIODS:
            errors["period"] = "must be 'morning' or 'night'"
        if errors:
            return jsonify(error="validation failed", details=errors), 400

        conn = get_db()
        with conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO routines (title, period, products, notes) "
                "VALUES (%s, %s, %s, %s) RETURNING *",
                (title, period, products, notes),
            )
            created = row_to_dict(cur.fetchone())
        conn.close()

        try:  # invalidate the cache so the next GET sees the new row
            get_cache().delete(CACHE_KEY)
        except redis.RedisError:
            pass

        resp = jsonify(created)
        resp.headers["Location"] = f"/api/routines/{created['id']}"
        return resp, 201

    return app


app = create_app() if os.environ.get("GLOWLOG_SKIP_INIT") != "1" else None
