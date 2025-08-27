# app/core/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys and URLs
    GPT4_API_KEY: str
    GPT4_API_URL: str

    # Application settings
    # The default value will create a 'temp_files' directory in the project root
    TEMP_BASE_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../", "temp_files")

    class Config:
        env_file = ".env"

settings = Settings()

# Ensure the temp directory exists on startup
os.makedirs(settings.TEMP_BASE_DIR, exist_ok=True)