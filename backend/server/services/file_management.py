import os
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
import mimetypes

from server.settings import ALLOWED_FILE_EXTENSIONS

class FileStorageService:
    """Service for managing file storage operations."""

    def __init__(self, base_dir:str = None) -> None:
        """Initializes the file storage service."""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def ensure_directories(self, dir_path: Path) -> None:
        """Ensures that a directory exists."""
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            Path(os.path.join(self.base_dir, "raw_data_dir")).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create directories: {e}")
    
    def calculate_file_hash(self, file_path: Path, algorithm: str = "sha256") -> str:
        """Calculates the hash of a file."""
        hash_func = hashlib.new(algorithm)
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def get_mime_type(self, file_path: Path) -> str:
        """Gets the MIME type of a file."""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"
    
    def is_allowed_file_type(self, filename:str, allowed_types: list) -> bool:
        """Checks if the file type is allowed."""
        file_allowed = Path(filename).suffix.lower() in allowed_types
        return file_allowed

    def sanitize_filename(self, filename: str) -> str:
        """Sanitizes the filename to prevent directory traversal attacks."""
        safe_characters = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        sanitized = ''.join(c for c in filename if c in safe_characters)

        if len(sanitized) > 100:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:100 - len(ext)] + ext
        
        return sanitized

    def store_file(self, file_name) -> dict:
        """Stores a file and returns its metadata."""
        self.ensure_directories(self.base_dir)
        
        sanitized_name = self.sanitize_filename(file_name)
        today_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        file_path = self.base_dir / "raw_data_dir" / today_date / sanitized_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist.")
        
        if not self.is_allowed_file_type(file_name, ALLOWED_FILE_EXTENSIONS):
            raise ValueError(f"File type not allowed: {file_name}")
        
        file_hash = self.calculate_file_hash(file_path)
        mime_type = self.get_mime_type(file_path)
        file_size = file_path.stat().st_size
        upload_time = datetime.utcnow().isoformat() + "Z"
        
        metadata = {
            "file_name": sanitized_name,
            "file_path": str(file_path),
            "file_size": file_size,
            "mime_type": mime_type,
            "file_hash": file_hash,
            "upload_time": upload_time
        }
        
        return metadata
    
    def file_exists(self, file_path:str) -> bool:
        """Checks if a file exists in the storage."""
        full_path = self.base_dir / file_path
        return full_path.exists()
        
    def get_file_by_path(self, file_path: str) -> Path:
        """Retrieves a file by its path."""
        full_path = self.base_dir / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File {full_path} does not exist.")
        return full_path
    
    def delete_file(self, file_path: str) -> bool:
        """Deletes a file from the storage."""
        full_path = self.base_dir / file_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    
    def get_file_metadata(self, file_path: str) -> dict:
        """Retrieves metadata of a file."""
        full_path = self.base_dir / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File {full_path} does not exist.")
        
        file_hash = self.calculate_file_hash(full_path)
        mime_type = self.get_mime_type(full_path)
        file_size = full_path.stat().st_size
        upload_time = datetime.utcfromtimestamp(full_path.stat().st_ctime).isoformat() + "Z"
        
        metadata = {
            "file_name": full_path.name,
            "file_path": str(full_path),
            "file_size": file_size,
            "mime_type": mime_type,
            "file_hash": file_hash,
            "upload_time": upload_time
        }
        
        return metadata
        

