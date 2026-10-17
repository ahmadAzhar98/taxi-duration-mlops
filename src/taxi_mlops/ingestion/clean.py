import logging

import pandas as pd

from taxi_mlops.ingestion.schemas import (
    MAX_DURATION_MIN,
    MAX_ZONE_ID,
    MIN_DURATION_MIN,
    MIN_ZONE_ID,
    CleanTripSchema,
    RawTripSchema,
)

logger = logging.getLogger(__name__)

CLEAN_COLUMNS = list(CleanTripSchema.to_schema().columns)


def month_bounds(month: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    start = pd.Timestamp(f"{month}-01")
    return start, start + pd.offsets.MonthBegin(1)


def clean_trips(raw: pd.DataFrame, month: str) -> pd.DataFrame:
    """Validate a raw TLC month, drop invalid trips, and return data matching CleanTripSchema."""
    df = RawTripSchema.validate(raw)
    df = df.rename(
        columns={
            "tpep_pickup_datetime": "pickup_datetime",
            "tpep_dropoff_datetime": "dropoff_datetime",
        }
    )
    df["duration_min"] = (
        df["dropoff_datetime"] - df["pickup_datetime"]
    ).dt.total_seconds() / 60

    start, end = month_bounds(month)
    rules = {
        "pickup_outside_month": ~df["pickup_datetime"].between(start, end, inclusive="left"),
        "duration_out_of_range": ~df["duration_min"].between(MIN_DURATION_MIN, MAX_DURATION_MIN),
        "non_positive_distance": df["trip_distance"] <= 0,
        "invalid_zone": ~(
            df["PULocationID"].between(MIN_ZONE_ID, MAX_ZONE_ID)
            & df["DOLocationID"].between(MIN_ZONE_ID, MAX_ZONE_ID)
        ),
        "negative_passengers": df["passenger_count"] < 0,
    }
    drop = pd.Series(False, index=df.index)
    for name, mask in rules.items():
        logger.info("%s: %d rows flagged by %s", month, mask.sum(), name)
        drop |= mask

    clean = df.loc[~drop, CLEAN_COLUMNS].reset_index(drop=True)
    logger.info(
        "%s: kept %d / %d rows (%.1f%%)", month, len(clean), len(raw), 100 * len(clean) / len(raw)
    )
    return CleanTripSchema.validate(clean)
