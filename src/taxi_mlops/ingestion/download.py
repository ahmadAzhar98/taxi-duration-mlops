import logging
import tempfile

import requests

from taxi_mlops import storage
from taxi_mlops.config import settings

logger = logging.getLogger(__name__)


def month_url(month: str) -> str:
    return f"{settings.tlc_base_url}/{settings.taxi_type}_tripdata_{month}.parquet"


def raw_uri(month: str) -> str:
    return storage.uri(settings.raw_bucket, f"{settings.taxi_type}_tripdata_{month}.parquet")


def download_month(month: str, force: bool = False) -> str:
    """Copy one month of TLC trip data into the raw bucket; skips months already there."""
    dest = raw_uri(month)
    if storage.exists(dest) and not force:
        logger.info("Skipping %s, already in object storage", dest)
        return dest

    logger.info("Downloading %s", month_url(month))
    # Stage locally and upload only after a complete download, so a failed
    # transfer never leaves a truncated object in the bucket
    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
        with requests.get(month_url(month), stream=True, timeout=60) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=1 << 20):
                tmp.write(chunk)
        tmp.flush()
        storage.filesystem().put_file(tmp.name, dest)
    logger.info("Uploaded %s", dest)
    return dest
