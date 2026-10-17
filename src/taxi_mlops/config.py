from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Project settings; override any field with a TAXI_-prefixed env var or .env entry."""

    model_config = SettingsConfigDict(
        env_prefix="TAXI_", env_file=PROJECT_ROOT / ".env", extra="ignore"
    )

    tlc_base_url: str = "https://d37ci6vzurychx.cloudfront.net/trip-data"
    taxi_type: str = "yellow"

    train_months: list[str] = ["2024-01", "2024-02", "2024-03"]
    replay_months: list[str] = [f"2024-{m:02d}" for m in range(4, 13)]

    # Object storage (RustFS locally, any S3-compatible service elsewhere).
    # Standard AWS variable names so boto3, s3fs and Feast all pick them up too.
    s3_endpoint_url: str = Field("http://localhost:9010", validation_alias="AWS_ENDPOINT_URL")
    aws_access_key_id: str = Field("rustfsadmin", validation_alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field("rustfsadmin", validation_alias="AWS_SECRET_ACCESS_KEY")
    raw_bucket: str = "raw"
    processed_bucket: str = "processed"
    features_bucket: str = "features"

    feature_repo_dir: Path = PROJECT_ROOT / "feature_repo"


settings = Settings()
