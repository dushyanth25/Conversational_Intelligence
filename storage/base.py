from abc import ABC, abstractmethod
from typing import BinaryIO, Dict, Optional

from .models import ObjectMetadata


class ObjectStorage(ABC):
    @abstractmethod
    def put_object(self, object_name: str, data: BinaryIO, length: int = -1, content_type: str = "application/octet-stream", metadata: Optional[Dict[str, str]] = None) -> ObjectMetadata:
        pass
        
    @abstractmethod
    def get_object(self, object_name: str) -> BinaryIO:
        pass
        
    @abstractmethod
    def exists(self, object_name: str) -> bool:
        pass
        
    @abstractmethod
    def delete_object(self, object_name: str) -> None:
        pass
        
    @abstractmethod
    def get_metadata(self, object_name: str) -> ObjectMetadata:
        pass
