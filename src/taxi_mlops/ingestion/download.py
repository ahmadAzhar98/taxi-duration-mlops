import logging
from pathlib import Path

import requests

from taxi_mlops.config import settings

logger = logging.getLogger(__name__)


def month_url(month: str) -> str:
    return f"{settings.tlc_base_url}/{settings.taxi_type}_tripdata_{month}.parquet"


def raw_path(month: str) -> Path:
    return settings.raw_dir / f"{settings.taxi_type}_tripdata_{month}.parquet"


def download_month(month: str, force: bool = False) -> Path:
    """Download one month of TLC trip data; skips the download if the file already exists."""
    dest = raw_path(month)
    if dest.exists() and not force:
        logger.info("Skipping %s, already downloaded", dest.name)
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    logger.info("Downloading %s", month_url(month))
    with requests.get(month_url(month), stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    # Rename only after a complete download so a crash never leaves a truncated file behind
    tmp.rename(dest)
    return dest
