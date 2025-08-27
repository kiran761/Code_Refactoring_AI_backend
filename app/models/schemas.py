# app/models/schemas.py
from pydantic import BaseModel
from typing import Dict, Any

class RefactorResponse(BaseModel):
    download_url: str
    structure: Dict[str, Any]
    session_id: str
    zip_name: str

class FileContentResponse(BaseModel):
    content: str
    file_path: str