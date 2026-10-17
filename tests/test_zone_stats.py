import pandas as pd
import pytest

from taxi_mlops.features.zone_stats import build_zone_hourly_stats

START = pd.Timestamp("2024-01-15 09:00")
END = pd.Timestamp("2024-01-15 12:00")


def trip(zone: int, pickup: str, dropoff: str, distance: float = 1.0) -> dict:
    pickup_ts, dropoff_ts = pd.Timestamp(pickup), pd.Timestamp(dropoff)
    return {
        "PULocationID": zone,
        "pickup_datetime": pickup_ts,
        "dropoff_datetime": dropoff_ts,
        "trip_distance": distance,
        "duration_min": (dropoff_ts - pickup_ts).total_seconds() / 60,
    }


@pytest.fixture
def stats() -> pd.DataFrame:
    trips = pd.DataFrame(
        [
            trip(1, "2024-01-15 09:05", "2024-01-15 09:15", distance=2.0),
            trip(1, "2024-01-15 09:30", "2024-01-15 09:50", distance=4.0),
            # Picked up in the 09:00 hour but finishes at 10:10, so it counts toward 10:00-11:00
            trip(1, "2024-01-15 09:55", "2024-01-15 10:10"),
            trip(2, "2024-01-15 11:00", "2024-01-15 11:30"),
            # Outside [START, END), must be ignored
            trip(2, "2024-01-15 12:10", "2024-01-15 12:40"),
        ]
    )
    return build_zone_hourly_stats(trips, START, END).set_index(["pickup_zone", "event_timestamp"])


def test_stats_are_stamped_at_window_end(stats):
    row = stats.loc[(1, pd.Timestamp("2024-01-15 10:00"))]
    assert row["trip_count_1h"] == 2
    assert row["avg_duration_min_1h"] == pytest.approx(15)
    assert row["avg_distance_1h"] == pytest.approx(3)


def test_trips_are_bucketed_by_dropoff_hour(stats):
    assert stats.loc[(1, pd.Timestamp("2024-01-15 11:00")), "trip_count_1h"] == 1


def test_every_zone_hour_is_present_with_zero_counts(stats):
    assert len(stats) == 2 * 3  # 2 zones x 3 hours
    quiet = stats.loc[(2, pd.Timestamp("2024-01-15 10:00"))]
    assert quiet["trip_count_1h"] == 0
    assert pd.isna(quiet["avg_duration_min_1h"])


def test_trips_outside_range_are_ignored(stats):
    assert stats.xs(2, level="pickup_zone")["trip_count_1h"].sum() == 1
