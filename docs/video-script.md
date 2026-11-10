# Skrip Video Demo (target 4:00–4:30)

Rekam layar sederhana (QuickTime / OBS / Zoom) dengan **suara sendiri**. Bacakan dengan kata-kata Anda; skrip ini hanya kerangka.
Di deskripsi video cantumkan tautan GitHub dan artikel. Atur visibilitas **Public**.

| Waktu | Layar | Narasi (contoh) |
|---|---|---|
| 0:00–0:30 | Halaman README di GitHub | "Halo, saya `<nama>`, NIM `<nim>`. Projek saya GlowLog, web untuk mencatat rutinitas skincare pagi dan malam. Saya memilih ini karena kecil tapi memuat aplikasi, database, dan cache, jadi cocok untuk belajar Docker sebagai calon Cloud/DevOps Engineer." |
| 0:30–1:00 | Diagram arsitektur | "Ada tiga container dalam satu network `glowlog-net`: `web` Flask di port 8000, `db` PostgreSQL dengan named volume, dan `redis` sebagai cache. Hanya port 8000 yang dibuka ke localhost. Antar-container saling memanggil lewat nama service." |
| 1:00–2:15 | `app/Dockerfile` | Jelaskan **berurutan, per baris** (lihat daftar A di bawah). |
| 2:15–3:20 | `docker-compose.yml` | Jelaskan **per blok** (lihat daftar B di bawah). |
| 3:20–4:10 | Terminal + browser | Demo: `cp .env.example .env` → `docker compose up -d --build` → `docker compose ps` (tunjukkan `healthy`) → buka `http://localhost:8000`, tambah rutinitas → `curl -i` GET `/health` (200), POST (201), GET dua kali (`MISS` lalu `HIT`). |
| 4:10–4:40 | Terminal | Uji persistensi: `docker compose down` → `docker compose up -d` → refresh, data masih ada. Jelaskan `down -v` akan menghapus volume sehingga data hilang. Tutup: "Terima kasih." |

## A. Poin penjelasan Dockerfile (satu per baris/blok)

* `FROM python:3.12.7-slim-bookworm AS builder`: base image dengan **tag versi spesifik** agar reproducible; `AS builder` memberi nama stage pertama.
* `WORKDIR /build`: direktori kerja di stage builder.
* `ENV PIP_NO_CACHE_DIR=1 ...`: pip tidak menyimpan cache sehingga layer lebih kecil.
* `COPY requirements.txt .`: salin **dependency dulu** agar layer cache dipakai ulang.
* `RUN pip install --prefix=/install ...`: pasang paket ke folder `/install` yang nanti diambil stage kedua.
* `FROM ... AS runtime`: stage kedua yang menjadi image akhir (multi-stage → kecil).
* `ENV PYTHONUNBUFFERED=1 ...`: log langsung keluar; tidak membuat file `.pyc`. `PORT=8000` informasi port.
* `WORKDIR /app`: direktori kerja aplikasi.
* `RUN useradd ...`: membuat user non-root untuk keamanan.
* `COPY --from=builder /install /usr/local`: ambil hanya paket hasil build dari stage builder.
* `COPY --chown=... . .`: salin source code **setelah** dependency. Pakai `COPY`, bukan `ADD`, karena tidak butuh unduh URL atau ekstrak otomatis.
* `USER glowlog`: proses berjalan sebagai non-root.
* `EXPOSE 8000`: dokumentasi port aplikasi (belum membuka ke host; itu tugas `ports` di Compose).
* `HEALTHCHECK ...`: Docker memeriksa `/health` secara berkala.
* `CMD ["gunicorn", ...]`: **exec form**, gunicorn jadi PID 1 dan menerima SIGTERM.
* Sebut `.dockerignore`: mengecualikan `.git`, `.env`, `tests/`.

## B. Poin penjelasan docker-compose.yml

* `name: glowlog`: nama project Compose (prefix nama resource).
* `web`: `build.context: ./app` membangun dari Dockerfile; `env_file: .env` membaca konfigurasi; `environment: DB_HOST: db, REDIS_HOST: redis` memakai **nama service**; `ports "${APP_PORT:-8000}:8000"` membuka ke localhost; `depends_on` dengan `condition: service_healthy` menunggu db dan redis siap; `networks` memasang ke `glowlog-net`; `restart: unless-stopped`.
* `db`: image `postgres:16.4-alpine` (tag versi); `env_file` memberi user/password/db; `volumes: glowlog-pgdata:/var/lib/postgresql/data` = **named volume**; `healthcheck` memakai `pg_isready` (`$$` agar variabel dibaca di dalam container, bukan oleh Compose).
* `redis`: `command` mematikan persistensi karena hanya cache; `healthcheck: redis-cli ping`.
* `adminer`: `profiles: ["tools"]` hanya jalan dengan `--profile tools`; `ADMINER_DEFAULT_SERVER: db`.
* `volumes:` mendeklarasikan named volume; `networks:` mendeklarasikan network user-defined `glowlog-net` (driver bridge).
