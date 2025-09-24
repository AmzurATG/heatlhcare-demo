import os
from pathlib import Path

def ensure_upload_dir():
    """Ensure upload directory exists"""
    upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads"))
    upload_dir.mkdir(exist_ok=True)
    return upload_dir

def cleanup_old_files(directory: Path, max_age_hours: int = 24):
    """Clean up old files from upload directory"""
    import time
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for file_path in directory.glob("*"):
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                    print(f"Cleaned up old file: {file_path}")
                except Exception as e:
                    print(f"Error cleaning up file {file_path}: {e}")

def validate_date_format(date_string: str) -> bool:
    """Validate date format is YYYY-MM-DD"""
    try:
        from datetime import datetime
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False
