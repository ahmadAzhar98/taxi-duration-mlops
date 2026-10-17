"""Compute hourly pickup-zone stats for TLC months and write them to the features bucket.

Usage: uv run python -m taxi_mlops.features.run [MONTH ...]
Defaults to the configured training months.
"""

import argparse
import logging

import pandas as pd

from taxi_mlops import storage
from taxi_mlops.config import settings
from taxi_mlops.features.zone_stats import build_zone_hourly_stats
from taxi_mlops.ingestion.clean import month_bounds
from taxi_mlops.ingestion.run import processed_uri

logger = logging.getLogger(__name__)

ZONE_STATS_PREFIX = "zone_hourly_stats"


def zone_stats_uri(month: str) -> str:
    return storage.uri(settings.features_bucket, f"{ZONE_STATS_PREFIX}/{month}.parquet")


def previous_month(month: str) -> str:
    return (pd.Period(month, freq="M") - 1).strftime("%Y-%m")


def build_month(month: str) -> str:
    # Trips picked up late last month can drop off this month, so they belong
    # in this month's first windows; include the previous month when available
    sources = [processed_uri(m) for m in (previous_month(month), month)]
    trips = pd.concat(
        [storage.read_parquet(uri) for uri in sources if storage.exists(uri)],
        ignore_index=True,
    )
    start, end = month_bounds(month)
    stats = build_zone_hourly_stats(trips, start, end)

    dest = zone_stats_uri(month)
    storage.write_parquet(stats, dest)
    logger.info("Wrote %d zone-hour rows to %s", len(stats), dest)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("months", nargs="*", default=settings.train_months)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    for month in args.months:
        build_month(month)


if __name__ == "__main__":
    main()
