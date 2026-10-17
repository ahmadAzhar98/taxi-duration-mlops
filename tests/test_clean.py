import pandas as pd
import pandera.errors
import pytest

from taxi_mlops.ingestion.clean import clean_trips


def make_raw(**overrides) -> pd.DataFrame:
    row = {
        "VendorID": 2,
        "tpep_pickup_datetime": pd.Timestamp("2024-01-15 10:00"),
        "tpep_dropoff_datetime": pd.Timestamp("2024-01-15 10:20"),
        "passenger_count": 1.0,
        "trip_distance": 3.2,
        "RatecodeID": 1.0,
        "PULocationID": 161,
        "DOLocationID": 237,
        "payment_type": 1,
        "fare_amount": 18.0,  # extra raw column, should be dropped
    }
    row.update(overrides)
    return pd.DataFrame([row])


def test_valid_trip_is_kept_with_duration():
    clean = clean_trips(make_raw(), "2024-01")
    assert len(clean) == 1
    assert clean.loc[0, "duration_min"] == pytest.approx(20)
    assert "fare_amount" not in clean.columns


@pytest.mark.parametrize(
    "overrides",
    [
        {"tpep_pickup_datetime": pd.Timestamp("2002-12-31 23:00")},  # outside month
        {"tpep_dropoff_datetime": pd.Timestamp("2024-01-15 09:50")},  # negative duration
        {"tpep_dropoff_datetime": pd.Timestamp("2024-01-15 10:00:30")},  # under 1 minute
        {"tpep_dropoff_datetime": pd.Timestamp("2024-01-15 12:00")},  # over 60 minutes
        {"trip_distance": 0.0},
        {"PULocationID": 300},
    ],
)
def test_invalid_trips_are_dropped(overrides):
    assert clean_trips(make_raw(**overrides), "2024-01").empty


def test_missing_passenger_count_is_allowed():
    clean = clean_trips(make_raw(passenger_count=None, RatecodeID=None), "2024-01")
    assert len(clean) == 1


def test_missing_required_column_fails_raw_validation():
    with pytest.raises(pandera.errors.SchemaError):
        clean_trips(make_raw().drop(columns="PULocationID"), "2024-01")
