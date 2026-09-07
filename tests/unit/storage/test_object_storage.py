import io
from unittest.mock import MagicMock, patch

import pytest
import urllib3
from minio.error import S3Error

from config.settings import Settings
from storage.exceptions import (
    BucketMissingError,
    ObjectNotFoundError,
    StorageAuthenticationError,
    StorageConnectionError,
    UploadError,
)
from storage.minio.minio_storage import MinIOStorage


@pytest.fixture
def mock_settings():
    return Settings(
        MINIO_ENDPOINT="localhost:9000",
        MINIO_ACCESS_KEY="minioadmin",
        MINIO_SECRET_KEY="minioadmin",
        MINIO_BUCKET="test-bucket",
        MINIO_SECURE=False,
    )

@pytest.fixture
def mock_minio():
    with patch("storage.minio.minio_storage.Minio") as mock:
        client_mock = MagicMock()
        mock.return_value = client_mock
        client_mock.bucket_exists.return_value = True
        yield client_mock

@pytest.fixture
def storage(mock_settings, mock_minio):
    with patch("storage.minio.minio_storage.get_settings", return_value=mock_settings):
        return MinIOStorage()

def test_bucket_missing(mock_settings, mock_minio):
    mock_minio.bucket_exists.return_value = False
    with patch("storage.minio.minio_storage.get_settings", return_value=mock_settings):
        with pytest.raises(BucketMissingError):
            MinIOStorage()

def test_authentication_error(mock_settings, mock_minio):
    mock_minio.bucket_exists.side_effect = S3Error(
        code="AccessDenied", message="denied", resource="", request_id="", host_id="", response=None
    )
    with patch("storage.minio.minio_storage.get_settings", return_value=mock_settings):
        with pytest.raises(StorageAuthenticationError):
            MinIOStorage()

def test_connection_error(mock_settings, mock_minio):
    mock_minio.bucket_exists.side_effect = urllib3.exceptions.MaxRetryError(None, None)
    with patch("storage.minio.minio_storage.get_settings", return_value=mock_settings):
        with pytest.raises(StorageConnectionError):
            MinIOStorage()

def test_upload(storage, mock_minio):
    mock_minio.stat_object.return_value = MagicMock(
        object_name="test.txt",
        size=100,
        content_type="text/plain",
        last_modified=None,
        metadata={}
    )
    
    data = io.BytesIO(b"hello world")
    metadata = storage.put_object("test.txt", data, length=11, content_type="text/plain")
    
    mock_minio.put_object.assert_called_once()
    assert metadata.object_name == "test.txt"
    assert metadata.size == 100

def test_upload_missing_length(storage, mock_minio):
    mock_minio.stat_object.return_value = MagicMock(
        object_name="test.txt",
        size=11,
        content_type="text/plain",
        last_modified=None,
        metadata={}
    )
    
    data = io.BytesIO(b"hello world")
    storage.put_object("test.txt", data, length=-1, content_type="text/plain")
    
    call_args = mock_minio.put_object.call_args[0]
    assert call_args[3] == 11

def test_upload_failure(storage, mock_minio):
    mock_minio.put_object.side_effect = Exception("failed")
    data = io.BytesIO(b"")
    with pytest.raises(UploadError):
        storage.put_object("test.txt", data, length=0)

def test_download(storage, mock_minio):
    mock_response = MagicMock()
    mock_minio.get_object.return_value = mock_response
    
    res = storage.get_object("test.txt")
    assert res == mock_response
    mock_minio.get_object.assert_called_once_with(storage.bucket, "test.txt")

def test_download_missing_object(storage, mock_minio):
    mock_minio.get_object.side_effect = S3Error(
        code="NoSuchKey", message="missing", resource="", request_id="", host_id="", response=None
    )
    with pytest.raises(ObjectNotFoundError):
        storage.get_object("missing.txt")

def test_exists(storage, mock_minio):
    mock_minio.stat_object.return_value = MagicMock()
    assert storage.exists("test.txt") is True

def test_not_exists(storage, mock_minio):
    mock_minio.stat_object.side_effect = S3Error(
        code="NoSuchKey", message="missing", resource="", request_id="", host_id="", response=None
    )
    assert storage.exists("test.txt") is False

def test_metadata(storage, mock_minio):
    mock_minio.stat_object.return_value = MagicMock(
        object_name="test.txt",
        size=123,
        content_type="text/plain",
        last_modified=None,
        metadata={"custom": "value"}
    )
    
    meta = storage.get_metadata("test.txt")
    assert meta.object_name == "test.txt"
    assert meta.size == 123
    assert meta.metadata == {"custom": "value"}

def test_metadata_missing(storage, mock_minio):
    mock_minio.stat_object.side_effect = S3Error(
        code="NoSuchKey", message="missing", resource="", request_id="", host_id="", response=None
    )
    with pytest.raises(ObjectNotFoundError):
        storage.get_metadata("test.txt")
