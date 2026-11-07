from pydantic import BaseModel
from typing import List, Optional


class DriveFile(BaseModel):
    id: str
    name: str
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None


class Folder(BaseModel):
    url: str
    name: str
    files: List[DriveFile]
