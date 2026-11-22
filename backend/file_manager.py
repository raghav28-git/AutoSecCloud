import os
import zipfile
import shutil
import tempfile
import uuid
from typing import Tuple

MAX_ZIP_SIZE = 50 * 1024 * 1024  # 50 MB limit
MAX_FILE_COUNT = 1000
MAX_UNCOMPRESSED_SIZE = 200 * 1024 * 1024  # 200 MB limit

def create_job_workspace() -> Tuple[str, str]:
    """Creates a temporary workspace for a deployment job."""
    job_id = str(uuid.uuid4())
    base_dir = os.path.join(tempfile.gettempdir(), "autosec_cloud", job_id)
    os.makedirs(base_dir, exist_ok=True)
    extract_dir = os.path.join(base_dir, "src")
    os.makedirs(extract_dir, exist_ok=True)
    return base_dir, extract_dir

def safe_extract_zip(zip_path: str, extract_dir: str) -> int:
    """
    Safely extracts a ZIP archive into extract_dir with Zip-Slip path traversal protection (CWE-22)
    and Zip-Bomb resource limits.
    Returns the number of extracted files.
    """
    canonical_extract_dir = os.path.realpath(extract_dir)
    file_count = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(zip_path, 'r') as zf:
        infolist = zf.infolist()
        if len(infolist) > MAX_FILE_COUNT:
            raise ValueError(f"Zip bomb protection: Exceeded maximum allowed files count ({MAX_FILE_COUNT})")

        for member in infolist:
            file_count += 1
            total_uncompressed_bytes += member.file_size
            if total_uncompressed_bytes > MAX_UNCOMPRESSED_SIZE:
                raise ValueError(f"Zip bomb protection: Exceeded maximum uncompressed size ({MAX_UNCOMPRESSED_SIZE / (1024*1024)}MB)")

            # Resolve canonical path to prevent Zip-Slip path traversal
            target_path = os.path.realpath(os.path.join(extract_dir, member.filename))
            
            # Ensure the target path stays strictly inside the extract directory
            if not target_path.startswith(canonical_extract_dir + os.sep) and target_path != canonical_extract_dir:
                raise ValueError(f"Zip-Slip Security Guard Triggered: Unsafe file path detected in zip archive: '{member.filename}'")

        # Extraction phase
        zf.extractall(extract_dir)

    return file_count

def cleanup_workspace(base_dir: str):
    """Safely removes the job workspace folder after deployment."""
    if os.path.exists(base_dir):
        try:
            shutil.rmtree(base_dir)
        except Exception:
            pass
