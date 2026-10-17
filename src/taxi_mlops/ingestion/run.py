"""Download, validate and clean TLC months into object storage.

Usage: uv run python -m taxi_mlops.ingestion.run [MONTH ...]
Defaults to the configured training months.
"""

import argparse
import logging

from taxi_mlops import storage
from taxi_mlops.config import settings
from taxi_mlops.ingestion.clean import clean_trips
from taxi_mlops.ingestion.download import download_month

logger = logging.getLogger(__name__)


def processed_uri(month: str) -> str:
    return storage.uri(settings.processed_bucket, f"{settings.taxi_type}_clean_{month}.parquet")


def ingest_month(month: str, force: bool = False) -> str:
    dest = processed_uri(month)
    if storage.exists(dest) and not force:
        logger.info("Skipping %s, already processed", dest)
        return dest

    raw = storage.read_parquet(download_month(month, force=force))
    clean = clean_trips(raw, month)
    storage.write_parquet(clean, dest)
    logger.info("Wrote %s", dest)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("months", nargs="*", default=settings.train_months)
    parser.add_argument("--force", action="store_true", help="re-download and re-process")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    for month in args.months:
        ingest_month(month, force=args.force)


if __name__ == "__main__":
    main()
