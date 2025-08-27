# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import refactor
import time
import os
import shutil
from app.core.config import settings

app = FastAPI(
    title="Code Refactoring AI",
    description="An AI-powered tool to automatically refactor and modernize legacy codebases."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API endpoints from the router
app.include_router(refactor.router)

@app.on_event("startup")
def clean_temp_on_startup():
    """Clean up old session and zip files on startup."""
    try:
        if os.path.exists(settings.TEMP_BASE_DIR):
            for item in os.listdir(settings.TEMP_BASE_DIR):
                item_path = os.path.join(settings.TEMP_BASE_DIR, item)
                try:
                    # Clean directories and old zip files (e.g., older than 1 hour)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                    elif item.endswith('.zip') and (time.time() - os.path.getmtime(item_path)) > 3600:
                        os.remove(item_path)
                except OSError:
                    pass # Ignore errors if file is in use
    except Exception as e:
        print(f"Startup cleanup failed: {e}")