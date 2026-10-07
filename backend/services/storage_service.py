import logging

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from core.config import (
    STORAGE_ENDPOINT_URL,
    STORAGE_ACCESS_KEY_ID,
    STORAGE_SECRET_ACCESS_KEY,
    STORAGE_BUCKET,
)

logger = logging.getLogger(__name__)

# İstemci ilk kullanımda kurulur; ayarlar eksikse uygulama yine de açılır
_client = None


class StorageError(Exception):
    """Nesne depolama işlemi başarısız olduğunda fırlatılır."""


def is_configured() -> bool:
    return all([STORAGE_ENDPOINT_URL, STORAGE_ACCESS_KEY_ID, STORAGE_SECRET_ACCESS_KEY, STORAGE_BUCKET])


def _get_client():
    global _client
    if not is_configured():
        raise StorageError("Dosya depolama ayarları eksik.")

    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=STORAGE_ENDPOINT_URL,
            aws_access_key_id=STORAGE_ACCESS_KEY_ID,
            aws_secret_access_key=STORAGE_SECRET_ACCESS_KEY,
            region_name="auto",  # R2 bölge olarak "auto" istiyor
            config=Config(retries={"max_attempts": 3, "mode": "standard"}),
        )
    return _client


def upload_file(key: str, content: bytes, content_type: str):
    try:
        _get_client().put_object(Bucket=STORAGE_BUCKET, Key=key, Body=content, ContentType=content_type)
    except (BotoCoreError, ClientError) as e:
        logger.exception("Depolamaya yükleme başarısız: %s", key)
        raise StorageError("Dosya depolamaya yüklenemedi.") from e


def download_file(key: str) -> bytes:
    try:
        response = _get_client().get_object(Bucket=STORAGE_BUCKET, Key=key)
        return response["Body"].read()
    except (BotoCoreError, ClientError) as e:
        logger.exception("Depolamadan indirme başarısız: %s", key)
        raise StorageError("Dosya depolamadan indirilemedi.") from e


def delete_file(key: str):
    try:
        _get_client().delete_object(Bucket=STORAGE_BUCKET, Key=key)
    except (BotoCoreError, ClientError) as e:
        logger.exception("Depolamadan silme başarısız: %s", key)
        raise StorageError("Dosya depolamadan silinemedi.") from e
