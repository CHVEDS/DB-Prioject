"""File utilities for banking analysis platform."""

import os
import tempfile
from pathlib import Path
from typing import Optional, BinaryIO


def create_temp_file(suffix: str = "", prefix: str = "temp") -> str:
    """
    Create a temporary file with specified suffix and prefix.
    
    Args:
        suffix: File extension (e.g., '.pdf', '.xlsx')
        prefix: Filename prefix
        
    Returns:
        Path to the temporary file
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=prefix)
    temp_file.close()
    return temp_file.name


def validate_file_path(file_path: str) -> bool:
    """
    Validate if file path is safe and accessible.
    
    Args:
        file_path: Path to validate
        
    Returns:
        True if path is valid and safe, False otherwise
    """
    try:
        path = Path(file_path).resolve()
        # Check if path is within allowed directories
        workspace_root = Path.cwd().resolve()
        if not str(path).startswith(str(workspace_root)):
            return False
        
        # Check if file exists and is readable
        return path.exists() and os.access(path, os.R_OK)
    except Exception:
        return False


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        Size in MB as float
    """
    return os.path.getsize(file_path) / (1024 * 1024)


def safe_delete_file(file_path: str) -> bool:
    """
    Safely delete a file.
    
    Args:
        file_path: Path to file to delete
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False