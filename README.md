# NYC Taxi Trip Duration — MLOps

End-to-end MLOps project predicting NYC Yellow Taxi trip duration on real
[TLC trip record data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).

- **Training data:** Yellow Taxi, Jan–Mar 2024
- **Production replay:** Apr–Dec 2024, fed in month by month to observe real drift

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Docker.

```bash
uv sync
uv run pytest
```

## Layout

```
src/taxi_mlops/   # ingestion, features, training, serving, monitoring
feature_repo/     # Feast feature definitions
pipelines/        # orchestration flows
docker/           # Dockerfiles
data/             # raw/ and processed/ (git-ignored)
tests/
```
