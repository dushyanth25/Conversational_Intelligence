import io
from typing import BinaryIO, Dict, Optional

import urllib3
from minio import Minio
from minio.error import S3Error

from config.settings import get_settings

from ..base import ObjectStorage
from ..exceptions import (
    BucketMissingError,
    DownloadError,
    ObjectNotFoundError,
    StorageAuthenticationError,
    StorageConnectionError,
    StorageError,
    UploadError,
)
from ..models import ObjectMetadata


class MinIOStorage(ObjectStorage):
    def __init__(self):
        settings = get_settings()
        secret_key = settings.MINIO_SECRET_KEY.get_secret_value() if settings.MINIO_SECRET_KEY else ""
        
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=secret_key,
                secure=settings.MINIO_SECURE,
            )
        except Exception as e:
            raise StorageConnectionError(f"Failed to initialize MinIO client: {e}") from e
            
        self.bucket = settings.MINIO_BUCKET
        
        try:
            if not self.client.bucket_exists(self.bucket):
                raise BucketMissingError(f"Bucket {self.bucket} does not exist.")
        except S3Error as e:
            if e.code in ("AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch"):
                raise StorageAuthenticationError("Authentication failed") from e
            if e.code == "NoSuchBucket":
                raise BucketMissingError(f"Bucket {self.bucket} does not exist.") from e
            raise StorageConnectionError(f"Connection failed: {e}") from e
        except urllib3.exceptions.MaxRetryError as e:
            raise StorageConnectionError("Connection timeout or failure") from e
        except Exception as e:
            if "BucketMissingError" in str(type(e)):
                raise
            raise StorageError(f"Unexpected error: {e}") from e

    def put_object(
        self, 
        object_name: str, 
        data: BinaryIO, 
        length: int = -1, 
        content_type: str = "application/octet-stream", 
        metadata: Optional[Dict[str, str]] = None
    ) -> ObjectMetadata:
        try:
            if length == -1 and isinstance(data, (io.BytesIO, io.StringIO)):
                pos = data.tell()
                data.seek(0, io.SEEK_END)
                length = data.tell() - pos
                data.seek(pos)
                
            if length == -1:
                self.client.put_object(
                    self.bucket, object_name, data, length, part_size=10*1024*1024,
                    content_type=content_type, metadata=metadata
                )
            else:
                self.client.put_object(
                    self.bucket, object_name, data, length,
                    content_type=content_type, metadata=metadata
                )
            return self.get_metadata(object_name)
        except S3Error as e:
            if e.code in ("AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch"):
                raise StorageAuthenticationError("Authentication failed") from e
            raise UploadError(f"Upload failed: {e}") from e
        except urllib3.exceptions.MaxRetryError as e:
            raise StorageConnectionError("Connection failed during upload") from e
        except Exception as e:
            raise UploadError(f"Unexpected upload error: {e}") from e

    def get_object(self, object_name: str) -> BinaryIO:
        try:
            response = self.client.get_object(self.bucket, object_name)
            return response
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise ObjectNotFoundError(f"Object {object_name} not found in {self.bucket}") from e
            raise DownloadError(f"Download failed: {e}") from e
        except urllib3.exceptions.MaxRetryError as e:
            raise StorageConnectionError("Connection failed during download") from e
        except Exception as e:
            raise DownloadError(f"Unexpected download error: {e}") from e

    def exists(self, object_name: str) -> bool:
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            if e.code in ("AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch"):
                raise StorageAuthenticationError("Authentication failed") from e
            raise StorageError(f"Error checking existence: {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error: {e}") from e

    def delete_object(self, object_name: str) -> None:
        try:
            self.client.remove_object(self.bucket, object_name)
        except S3Error as e:
            if e.code in ("AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch"):
                raise StorageAuthenticationError("Authentication failed") from e
            raise StorageError(f"Delete failed: {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected delete error: {e}") from e

    def get_metadata(self, object_name: str) -> ObjectMetadata:
        try:
            stat = self.client.stat_object(self.bucket, object_name)
            return ObjectMetadata(
                object_name=stat.object_name,
                size=stat.size,
                content_type=stat.content_type,
                last_modified=stat.last_modified,
                metadata=stat.metadata
            )
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise ObjectNotFoundError(f"Object {object_name} not found in {self.bucket}") from e
            if e.code in ("AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch"):
                raise StorageAuthenticationError("Authentication failed") from e
            raise StorageError(f"Failed to get metadata: {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected metadata error: {e}") from e
