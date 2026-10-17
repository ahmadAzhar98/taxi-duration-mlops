import pandas as pd
import pandera.pandas as pa
from pandera.typing import Series

MIN_DURATION_MIN = 1
MAX_DURATION_MIN = 60
# TLC taxi zones are numbered 1-265 (264 = unknown, 265 = outside NYC)
MIN_ZONE_ID, MAX_ZONE_ID = 1, 265


class RawTripSchema(pa.DataFrameModel):
    """Contract for the TLC file itself: the columns we rely on exist with usable types.

    No value checks here; dirty rows are expected and handled by cleaning.
    """

    VendorID: Series[int] = pa.Field(coerce=True)
    tpep_pickup_datetime: Series[pd.Timestamp] = pa.Field(coerce=True)
    tpep_dropoff_datetime: Series[pd.Timestamp] = pa.Field(coerce=True)
    passenger_count: Series[float] = pa.Field(nullable=True, coerce=True)
    trip_distance: Series[float] = pa.Field(coerce=True)
    RatecodeID: Series[float] = pa.Field(nullable=True, coerce=True)
    PULocationID: Series[int] = pa.Field(coerce=True)
    DOLocationID: Series[int] = pa.Field(coerce=True)
    payment_type: Series[int] = pa.Field(coerce=True)

    class Config:
        strict = False  # TLC files carry extra fare columns we don't use


class CleanTripSchema(pa.DataFrameModel):
    """Contract for cleaned trips handed to feature engineering and training."""

    VendorID: Series[int]
    pickup_datetime: Series[pd.Timestamp]
    dropoff_datetime: Series[pd.Timestamp]
    passenger_count: Series[float] = pa.Field(nullable=True, ge=0)
    trip_distance: Series[float] = pa.Field(gt=0)
    RatecodeID: Series[float] = pa.Field(nullable=True)
    PULocationID: Series[int] = pa.Field(ge=MIN_ZONE_ID, le=MAX_ZONE_ID)
    DOLocationID: Series[int] = pa.Field(ge=MIN_ZONE_ID, le=MAX_ZONE_ID)
    payment_type: Series[int] = pa.Field(ge=0)
    duration_min: Series[float] = pa.Field(ge=MIN_DURATION_MIN, le=MAX_DURATION_MIN)

    @pa.dataframe_check
    def dropoff_after_pickup(cls, df: pd.DataFrame) -> Series[bool]:
        return df["dropoff_datetime"] > df["pickup_datetime"]

    class Config:
        strict = True
        ordered = True
