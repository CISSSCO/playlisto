from pydantic import BaseModel
from typing import List


class DriveFile(BaseModel):
    id: str
    name: str


class Folder(BaseModel):
    url: str
    name: str
    files: List[DriveFile]
