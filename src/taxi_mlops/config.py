from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Project settings; override any field with a TAXI_-prefixed env var or .env entry."""

    model_config = SettingsConfigDict(env_prefix="TAXI_", env_file=".env", extra="ignore")

    data_dir: Path = PROJECT_ROOT / "data"
    tlc_base_url: str = "https://d37ci6vzurychx.cloudfront.net/trip-data"
    taxi_type: str = "yellow"

    train_months: list[str] = ["2024-01", "2024-02", "2024-03"]
    replay_months: list[str] = [f"2024-{m:02d}" for m in range(4, 13)]

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"


settings = Settings()
