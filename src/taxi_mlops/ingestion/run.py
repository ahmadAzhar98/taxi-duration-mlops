"""Download, validate and clean TLC months.

Usage: uv run python -m taxi_mlops.ingestion.run [MONTH ...]
Defaults to the configured training months.
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

from taxi_mlops.config import settings
from taxi_mlops.ingestion.clean import clean_trips
from taxi_mlops.ingestion.download import download_month

logger = logging.getLogger(__name__)


def processed_path(month: str) -> Path:
    return settings.processed_dir / f"{settings.taxi_type}_clean_{month}.parquet"


def ingest_month(month: str, force: bool = False) -> Path:
    dest = processed_path(month)
    if dest.exists() and not force:
        logger.info("Skipping %s, already processed", dest.name)
        return dest

    raw = pd.read_parquet(download_month(month))
    clean = clean_trips(raw, month)
    dest.parent.mkdir(parents=True, exist_ok=True)
    clean.to_parquet(dest, index=False)
    logger.info("Wrote %s", dest)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("months", nargs="*", default=settings.train_months)
    parser.add_argument("--force", action="store_true", help="re-process existing outputs")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    for month in args.months:
        ingest_month(month, force=args.force)


if __name__ == "__main__":
    main()
