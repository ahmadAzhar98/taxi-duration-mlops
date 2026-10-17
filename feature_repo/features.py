import os
from datetime import timedelta

from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float64, Int64

pickup_zone = Entity(
    name="pickup_zone",
    join_keys=["pickup_zone"],
    description="NYC TLC taxi zone where the trip started (1-265)",
)

zone_hourly_stats_source = FileSource(
    name="zone_hourly_stats_source",
    path="s3://features/zone_hourly_stats/",
    timestamp_field="event_timestamp",
    s3_endpoint_override=os.environ.get("AWS_ENDPOINT_URL", "http://localhost:9000"),
)

zone_hourly_stats = FeatureView(
    name="zone_hourly_stats",
    entities=[pickup_zone],
    # Rows are hourly, so anything older than 2h means the pipeline has stalled;
    # return nulls rather than silently serving stale traffic conditions
    ttl=timedelta(hours=2),
    schema=[
        Field(name="trip_count_1h", dtype=Int64),
        Field(name="avg_duration_min_1h", dtype=Float64),
        Field(name="avg_distance_1h", dtype=Float64),
    ],
    source=zone_hourly_stats_source,
    online=True,
    description="Trips completed from each pickup zone in the last full hour",
)
