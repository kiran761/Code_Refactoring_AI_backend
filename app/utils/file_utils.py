# app/utils/file_utils.py
import os
import uuid
from app.core.config import settings

def create_temp_dir() -> str:
    """Creates a unique temporary directory for processing."""
    unique_dir = os.path.join(settings.TEMP_BASE_DIR, f"repo_{uuid.uuid4().hex}")
    os.makedirs(unique_dir, exist_ok=True)
    return unique_dir

def build_nested_tree(path: str, root_path: str) -> dict:
    """Builds a nested dictionary representing the file structure."""
    tree = {}
    for root, dirs, files in os.walk(path):
        rel_root = os.path.relpath(root, root_path)
        current_level = tree
        if rel_root != '.':
            parts = rel_root.split(os.sep)
            for part in parts:
                current_level = current_level.setdefault(part, {})
        for file in files:
            current_level[file] = None
    return tree

def get_file_content(file_path: str) -> str:
    """Reads the content of a file safely."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        return "Binary file - content cannot be displayed"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def parse_github_url(url: str) -> tuple[str, str]:
    """Parses a GitHub URL to separate the repo URL from a subdirectory path."""
    if '/tree/' in url:
        parts = url.split('/tree/')
        repo_url = parts[0]
        branch_and_path = parts[1].split('/', 1)
        subdirectory = branch_and_path[1] if len(branch_and_path) > 1 else ""
        return repo_url, subdirectory
    return url, ""