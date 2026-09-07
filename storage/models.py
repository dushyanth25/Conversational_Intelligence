from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class ObjectMetadata(BaseModel):
    object_name: str
    size: int
    content_type: Optional[str]
    last_modified: Optional[datetime]
    metadata: Optional[Dict[str, str]]
