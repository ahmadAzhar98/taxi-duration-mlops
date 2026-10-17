"""Thin helpers around S3-compatible object storage (MinIO locally)."""

from functools import cache

import pandas as pd
import s3fs

from taxi_mlops.config import settings


def storage_options() -> dict:
    return {
        "key": settings.aws_access_key_id,
        "secret": settings.aws_secret_access_key,
        "client_kwargs": {"endpoint_url": settings.s3_endpoint_url},
    }


@cache
def filesystem() -> s3fs.S3FileSystem:
    return s3fs.S3FileSystem(**storage_options())


def uri(bucket: str, key: str) -> str:
    return f"s3://{bucket}/{key}"


def exists(path: str) -> bool:
    return filesystem().exists(path)


def read_parquet(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_parquet(path, storage_options=storage_options(), **kwargs)


def write_parquet(df: pd.DataFrame, path: str) -> None:
    df.to_parquet(path, index=False, storage_options=storage_options())
