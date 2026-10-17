# NYC Taxi Trip Duration — MLOps

End-to-end MLOps project predicting NYC Yellow Taxi trip duration on real
[TLC trip record data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).

- **Training data:** Yellow Taxi, Jan–Mar 2024 (~9.2M trips after cleaning)
- **Production replay:** Apr–Dec 2024, fed in month by month to observe real drift

## Architecture

```
TLC website ──► ingestion (Pandera validation) ──► s3://raw, s3://processed
                                                           │
                                         zone hourly stats ▼
                                                    s3://features ──► Feast
                                                                       ├─ offline store (parquet on S3) → training data
                                                                       └─ online store (SQLite)         → serving
```

| Component | Tool |
|---|---|
| Object storage | [RustFS](https://github.com/rustfs/rustfs) (S3-compatible, runs in Docker) |
| Data validation | Pandera |
| Feature store | Feast — parquet offline store, SQLite online store, local registry |
| Environment | uv (Python 3.11), Docker Compose |

All storage goes through the S3 API, so pointing `AWS_ENDPOINT_URL` and the
keys in `.env` at real AWS S3 works without code changes.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and a Docker engine
(e.g. [Colima](https://github.com/abiosoft/colima): `brew install colima docker-compose`).

```bash
colima start --cpu 4 --memory 8   # skip if you use Docker Desktop
cp .env.example .env
docker compose up -d              # starts RustFS and creates the buckets
uv sync
uv run pytest
```

RustFS listens on host port **9010** (S3 API) and **9011** (web console) to
avoid clashing with PHP-FPM, which often holds port 9000 on macOS.
Browse the buckets at http://localhost:9011 (login: `rustfsadmin` / `rustfsadmin`).

## Running the pipeline

```bash
# 1. Download, validate and clean months into s3://raw and s3://processed
uv run python -m taxi_mlops.ingestion.run            # defaults to training months
uv run python -m taxi_mlops.ingestion.run 2024-04    # or specific months

# 2. Build hourly pickup-zone features into s3://features
uv run python -m taxi_mlops.features.run

# 3. Register feature definitions with Feast (needs the S3 credentials in the environment)
set -a && source .env && set +a
cd feature_repo && uv run feast apply
```

Each step skips months that already exist; pass `--force` to ingestion to redo them.

## Features

Entity: **pickup zone** (`PULocationID`, 1–265). For every zone and hour:

| Feature | Description |
|---|---|
| `trip_count_1h` | Trips from the zone that completed in the last full hour |
| `avg_duration_min_1h` | Their mean duration (minutes) |
| `avg_distance_1h` | Their mean distance (miles) |

Trips are bucketed by **dropoff** time and each row is stamped at the end of
its hour, because a trip's duration is only known once it ends. Feast's
point-in-time join then only gives a trip the stats that existed before its
pickup, preventing label leakage.

## Layout

```
src/taxi_mlops/
├── config.py       # settings (months, buckets, S3 endpoint) from env / .env
├── storage.py      # S3 read/write helpers
├── ingestion/      # download, Pandera schemas, cleaning
├── features/       # zone hourly stats
├── training/
├── serving/
└── monitoring/
feature_repo/       # Feast config and feature definitions
pipelines/          # orchestration flows
tests/
docker-compose.yml  # RustFS + bucket creation
```
