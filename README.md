# GlowLog — Skincare Routine Tracker

A small multi-tier web app to log skincare products and your **morning / night** routines.
Built for the Cloud Computing midterm (COMP6991031): the focus is **containerization with Docker Compose** on localhost.

> **Author:** `<NAMA>` · `<NIM>` · `<KELAS>`

## Why this project

Skincare routines are easy to forget (which serum goes before moisturizer? did I use retinol yesterday?). GlowLog gives a
simple place to save a routine as an ordered list of products and view it by morning or night.
I chose it because it is small enough to finish in the exam window, yet it needs every layer I want to practice as a
Cloud/DevOps engineer: an app container, a stateful database with a volume, a cache, health checks, and env-based config.

**MVP feature:** add and view routines (morning / night).

## Architecture

![architecture](docs/architecture.png)

| Container | Image | Host port | Purpose |
|-----------|-------|-----------|---------|
| `web` | built from `app/Dockerfile` | `8000` | Flask + Gunicorn (HTML page + JSON API) |
| `db` | `postgres:16.4-alpine` | none (internal) | PostgreSQL with named volume `glowlog-pgdata` |
| `redis` | `redis:7.4.1-alpine` | none (internal) | Cache for `GET /api/routines` (**bonus**) |
| `adminer` | `adminer:4.8.1` | `8080` | DB UI, only with `--profile tools` |

All containers share the user-defined network `glowlog-net` and reach each other by **service name** (`db`, `redis`).

## Run it (3 commands)

Requirements: Docker + Docker Compose v2.

```bash
git clone <THIS-REPO-URL> glowlog && cd glowlog
cp .env.example .env            # edit the password if you like
docker compose up -d --build
```

Open **http://localhost:8000**.

```bash
docker compose ps                         # all services running, db + redis "healthy"
docker compose --profile tools up -d      # also start Adminer on http://localhost:8080
                                          #   System: PostgreSQL · Server: db · user/password/db from .env
docker compose down                       # stop, KEEP data (named volume stays)
docker compose down -v                    # stop and DELETE data (removes the volume)
```

## API

| Method | Path | Success | Errors |
|--------|------|---------|--------|
| GET | `/health` | `200` (db + redis ok) | `503` if a dependency is down |
| GET | `/api/routines?period=morning\|night` | `200` + JSON list, header `X-Cache: HIT/MISS` | `400` bad `period` |
| POST | `/api/routines` | `201 Created` + `Location` header | `400` validation error |

```bash
curl -i http://localhost:8000/health
curl -i -X POST http://localhost:8000/api/routines \
  -H "Content-Type: application/json" \
  -d '{"title":"Weekday glow","period":"morning","products":"Cleanser -> Serum -> SPF"}'
curl -i http://localhost:8000/api/routines
```

## Bonus: Redis cache (+5)

`GET /api/routines` uses the cache-aside pattern: the first call reads PostgreSQL (`X-Cache: MISS`) and stores the result in
Redis for `CACHE_TTL_SECONDS`; the next calls are served from Redis (`X-Cache: HIT`). A successful `POST` deletes the cache key
so data is never stale. Redis has a `redis-cli ping` healthcheck and the `web` service waits for it with
`depends_on: condition: service_healthy`. If Redis is down the API still works (`X-Cache: BYPASS`).

## Tests

```bash
docker compose up -d db redis        # needs ports, or run tests inside a container network
cd app && pip install -r requirements.txt pytest
DB_HOST=localhost REDIS_HOST=localhost POSTGRES_USER=... POSTGRES_PASSWORD=... POSTGRES_DB=... \
GLOWLOG_SKIP_INIT=1 pytest -q
```

## Security & data

* `.env` is git-ignored; only `.env.example` (dummy values) is committed. No secrets in the repo.
* Only dummy data is used. The app stores no personal data (no NIK, address, phone).
* The container runs as a non-root user; DB and Redis ports are not published to the host.

## Sources / credits

* [Flask](https://flask.palletsprojects.com/), [Gunicorn](https://gunicorn.org/), [psycopg2](https://www.psycopg.org/), [redis-py](https://github.com/redis/redis-py) — open-source libraries.
* Official Docker images: [postgres](https://hub.docker.com/_/postgres), [redis](https://hub.docker.com/_/redis), [adminer](https://hub.docker.com/_/adminer).

## Screenshots

> Replace with your own captures (see `docs/screenshots/`).

| | |
|--|--|
| App UI | `docs/screenshots/01-app.png` |
| `docker compose ps` | `docs/screenshots/02-compose-ps.png` |
| curl 200 / 201 | `docs/screenshots/03-curl.png` |
| Persistence test | `docs/screenshots/04-persistence.png` |

## Links

* Article: `<LINK-ARTIKEL>`
* Video demo: `<LINK-YOUTUBE>`

## AI Usage Declaration

I used an AI assistant (Claude) to help scaffold the code and draft documentation. I reviewed, ran and tested the code, and I can
explain every line of the Dockerfile and docker-compose.yml. `<Edit this paragraph so it truthfully reflects what you did.>`
