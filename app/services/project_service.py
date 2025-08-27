# app/services/project_service.py
import os
import shutil
import uuid
import zipfile
import asyncio
from typing import Optional
from fastapi import UploadFile
from git import Repo, GitCommandError
from app.services import openai_service
from app.utils.file_utils import create_temp_dir

async def process_project_files(source_dir: str, refactored_dir: str, language: str):
    """Iterates through files and calls the appropriate refactoring service."""
    tasks = []
    file_paths = []

    for root, _, files in os.walk(source_dir):
        if '.git' in root or 'node_modules' in root:
            continue
            
        rel_path = os.path.relpath(root, source_dir)
        dest_root = os.path.join(refactored_dir, rel_path) if rel_path != "." else refactored_dir
        os.makedirs(dest_root, exist_ok=True)

        for file in files:
            src_path = os.path.join(root, file)
            dest_path = os.path.join(dest_root, file)
            
            try:
                with open(src_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check if the file should be refactored
                is_java_refactorable = language == "java" and (file.endswith(".java") or file == "pom.xml")
                is_node_refactorable = language == "nodejs" and (file.endswith((".js", ".cjs", ".mjs")) or file == "package.json")

                if is_java_refactorable:
                    tasks.append(openai_service.refactor_java_code(content))
                    file_paths.append(dest_path)
                elif is_node_refactorable:
                    tasks.append(openai_service.refactor_nodejs_code(content, file))
                    file_paths.append(dest_path)
                else:
                    shutil.copy2(src_path, dest_path) # Copy other files directly
            
            except (UnicodeDecodeError, IOError):
                shutil.copy2(src_path, dest_path) # Copy binary/unreadable files
    
    # Run all refactoring tasks concurrently
    refactored_contents = await asyncio.gather(*tasks, return_exceptions=True)

    # Write the results
    for i, content in enumerate(refactored_contents):
        if not isinstance(content, Exception):
            with open(file_paths[i], 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            print(f"Failed to refactor {file_paths[i]}: {content}")
            # Optionally, copy the original file on failure
            # shutil.copy2(original_src_path, file_paths[i])


def handle_project_source(
    temp_dir: str,
    github_url: Optional[str] = None,
    zip_file: Optional[UploadFile] = None
) -> str:
    """Clones a Git repo or extracts a zip file into a temporary directory."""
    if github_url:
        from app.utils.file_utils import parse_github_url
        repo_url, subdirectory = parse_github_url(github_url)
        try:
            print(f"Cloning {repo_url} into {temp_dir}...")
            Repo.clone_from(repo_url, temp_dir, depth=1)
            source_dir = os.path.join(temp_dir, subdirectory) if subdirectory else temp_dir
            if subdirectory and not os.path.exists(source_dir):
                raise ValueError(f"Subdirectory '{subdirectory}' not found in repository.")
            return source_dir
        except GitCommandError as e:
            raise ValueError(f"Failed to clone repository. Check URL. Error: {e.stderr}")

    elif zip_file:
        zip_path = os.path.join(temp_dir, zip_file.filename)
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(zip_file.file, buffer)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        return temp_dir
    
    raise ValueError("Either GitHub URL or zip file must be provided.")

def create_zip_archive(source_dir: str) -> str:
    """Creates a zip archive from a directory and returns its path."""
    from app.core.config import settings
    zip_name = f"refactored_output_{uuid.uuid4().hex}.zip"
    zip_path = os.path.join(settings.TEMP_BASE_DIR, zip_name)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                zipf.write(full_path, arcname=rel_path)
    return zip_path