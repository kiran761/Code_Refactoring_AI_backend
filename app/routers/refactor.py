# app/routers/refactor.py
import os
import shutil
import uuid
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse

from app.models.schemas import RefactorResponse, FileContentResponse
from app.services import project_service
from app.utils import file_utils
from app.core.config import settings

router = APIRouter()

# A simple in-memory store for session data.
# WARNING: This is not production-ready. Data is lost on restart.
# For production, use a persistent store like Redis.
SESSIONS = {}

@router.post("/refactor-repo", response_model=RefactorResponse)
async def refactor_repo(
    language: str = Form(...),
    github_url: Optional[str] = Form(None),
    zip_file: Optional[UploadFile] = File(None)
):
    if language.lower() not in ["java", "nodejs"]:
        raise HTTPException(status_code=400, detail="Unsupported language. Use 'java' or 'nodejs'.")

    temp_dir = file_utils.create_temp_dir()
    refactored_dir = file_utils.create_temp_dir()

    try:
        source_dir = project_service.handle_project_source(temp_dir, github_url, zip_file)
        
        # This is a long-running task. It processes all files concurrently.
        await project_service.process_project_files(source_dir, refactored_dir, language.lower())
        
        # Zip the final output
        zip_path = project_service.create_zip_archive(refactored_dir)

        # Create session data
        session_id = uuid.uuid4().hex
        SESSIONS[session_id] = {
            'refactored_dir': refactored_dir,
            'created_at': time.time()
        }
        
        return RefactorResponse(
            download_url=f"/download/{os.path.basename(zip_path)}",
            structure=file_utils.build_nested_tree(refactored_dir, refactored_dir),
            session_id=session_id,
            zip_name=os.path.basename(zip_path)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"An unexpected server error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
    finally:
        # Clean up the initial temporary directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

@router.get("/file-content/{session_id}", response_model=FileContentResponse)
def get_file_content_endpoint(session_id: str, file_path: str):
    session_data = SESSIONS.get(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    
    refactored_dir = session_data['refactored_dir']
    full_file_path = os.path.realpath(os.path.join(refactored_dir, file_path))

    # Security check: Prevent directory traversal attacks
    if not full_file_path.startswith(os.path.realpath(refactored_dir)):
        raise HTTPException(status_code=400, detail="Invalid file path.")
    if not os.path.isfile(full_file_path):
        raise HTTPException(status_code=404, detail="File not found.")
        
    return FileContentResponse(
        content=file_utils.get_file_content(full_file_path),
        file_path=file_path
    )

@router.get("/download/{zip_name}")
def download_zip(zip_name: str):
    zip_path = os.path.join(settings.TEMP_BASE_DIR, zip_name)
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="File not found or expired.")
    return FileResponse(zip_path, media_type='application/zip', filename='refactored_output.zip')