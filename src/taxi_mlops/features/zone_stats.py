import pandas as pd

WINDOW = pd.Timedelta(hours=1)

FEATURE_COLUMNS = ["trip_count_1h", "avg_duration_min_1h", "avg_distance_1h"]


def build_zone_hourly_stats(
    trips: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    """Aggregate completed trips into hourly stats per pickup zone.

    A trip's duration is only known once it ends, so trips are bucketed by
    *dropoff* hour. Each row is stamped with the end of its window: stats for
    [09:00, 10:00) become available at 10:00, which is the timestamp Feast uses
    for point-in-time joins.

    Returns one row per (zone, hour) for windows starting in [start, end),
    including hours with no trips (count 0, averages NaN) so "quiet zone" is
    a signal rather than a missing row.
    """
    window_start = trips["dropoff_datetime"].dt.floor(WINDOW)
    in_range = window_start.between(start, end, inclusive="left")
    grouped = (
        trips[in_range]
        .assign(window_start=window_start[in_range])
        .groupby(["PULocationID", "window_start"])
        .agg(
            trip_count_1h=("duration_min", "size"),
            avg_duration_min_1h=("duration_min", "mean"),
            avg_distance_1h=("trip_distance", "mean"),
        )
    )

    zones = trips["PULocationID"].unique()
    hours = pd.date_range(start, end, freq=WINDOW, inclusive="left")
    full_index = pd.MultiIndex.from_product([zones, hours], names=grouped.index.names)
    stats = grouped.reindex(full_index)
    stats["trip_count_1h"] = stats["trip_count_1h"].fillna(0).astype("int64")

    return (
        stats.reset_index()
        .rename(columns={"PULocationID": "pickup_zone"})
        .assign(event_timestamp=lambda d: d["window_start"] + WINDOW)
        .drop(columns="window_start")
        .sort_values(["event_timestamp", "pickup_zone"], ignore_index=True)
        [["pickup_zone", "event_timestamp", *FEATURE_COLUMNS]]
    )
