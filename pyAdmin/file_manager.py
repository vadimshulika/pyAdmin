"""This class for file operations and system monitoring."""

import shutil
import zipfile
import inspect
from typing import List, Dict
from datetime import datetime
from pathlib import Path
from pyAdmin.utils import bytes_to_gb

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class FileManager:
    """A class to manage files, directories, and system monitoring.

    Provides methods to copy, move, compress files, and monitor resources.
    """

    def __init__(self):
        """Initiallize path to directories, which import this class."""
        frame = inspect.stack()[1]
        self.caller_dir = Path(frame.filename).parent.resolve()

    def _resolve_path(self, path: str) -> Path:
        """Convert path.

        Convert a relative path to an absolute path relative
        to the caller's directory.
        """
        return (self.caller_dir / path).resolve()

    def copy_file(self, source: str, destination: str) -> bool:
        """
        Copy a file from source to destination.

        Args:
            source (str): Path to the source file.
            destination (str): Path to the destination.

        Returns:
            bool: True if successful, False otherwise.
        """
        src = self._resolve_path(source)
        dest = self._resolve_path(destination)

        try:
            shutil.copy(src, dest)
            print(f"File {src} copied to {dest}")
            return True
        except Exception as e:
            print(f"Copy error: {str(e)}")
            return False

    def move_file(self, source: str, destination: str) -> bool:
        """
        Move a file from source to destination.

        Automatically creates destination directory if it doesn't exist.

        Args:
            source (str): Path to the source file.
            destination (str): Path to the destination.

        Returns:
            bool: True if successful, False otherwise.
        """
        src = self._resolve_path(source)
        dest = self._resolve_path(destination)

        try:
            dest_dir = dest.parent
            dest_dir.mkdir(parents=True, exist_ok=True)

            shutil.move(src, dest)
            print(f"File {src} moved to {dest}")
            return True
        except Exception as e:
            print(f"Move error: {str(e)}")
            return False

    def compress_files(self, files: List[str], zip_name: str) -> bool:
        """
        Create a ZIP archive from a list of files.

        Args:
            files (List[str]): List of file paths to compress.
            zip_name (str): Name of the output ZIP archive.

        Returns:
            bool: True if successful, False otherwise.
        """
        zip_path = self._resolve_path(zip_name)

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in files:
                    file_path = self._resolve_path(file)
                    if file_path.exists():
                        zipf.write(file_path, arcname=file_path.name)
                    else:
                        print(f"Warning: {file_path} does not exist")
            print(f"Archive {zip_path} created successfully")
            return True
        except Exception as e:
            print(f"Compression error: {str(e)}")
            return False
        
    def get_file_metadata(self, file_path: str) -> Dict:
        """
        Retrieve metadata of a specified file.

        Args:
            file_path (str): Path to the target file.

        Returns:
            Dict: Dictionary containing file metadata (size, creation time,
                  modification time, extension, permissions). Returns empty dict
                  if file does not exist or error occurs.
        """
        resolved_path = self._resolve_path(file_path)
        if not resolved_path.exists():
            print(f"File {resolved_path} does not exist")
            return {}

        try:
            stat = resolved_path.stat()
            creation_time = datetime.fromtimestamp(stat.st_ctime).strftime("%d.%m.%Y")
            modification_time = datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y")
            return {
                'size_bytes': stat.st_size,
                'creation_time': creation_time,
                'modification_time': modification_time,
                'extension': resolved_path.suffix,
                'permissions': oct(stat.st_mode)[-3:],
                'absolute_path': str(resolved_path.absolute())
            }
        except Exception as e:
            print(f"Metadata error: {str(e)}")
            return {}

    def get_system_status(self) -> Dict:
        """
        Get system resource usage (disk, memory, CPU).

        Returns:
            Dict: System status data or empty dict if psutil is not installed.
        """
        if not PSUTIL_AVAILABLE:
            print("psutil is required for this feature. ")
            print("Install it with 'pip install psutil'.")
            return {}

        status = {
            'disk': self._get_disk_usage(),
            'memory': self._get_memory_usage(),
            'cpu': self._get_cpu_usage()
        }
        return status

    def _get_disk_usage(self) -> Dict:
        """Get disk usage statistics for the root partition."""
        disk = psutil.disk_usage('/')
        return {
            'total_gb': bytes_to_gb(disk.total),
            'used_gb': bytes_to_gb(disk.used),
            'free_gb': bytes_to_gb(disk.free),
            'percent_used': disk.percent
        }

    def _get_memory_usage(self) -> Dict:
        """Get system memory usage statistics."""
        memory = psutil.virtual_memory()
        return {
            'total_gb': bytes_to_gb(memory.total),
            'available_gb': bytes_to_gb(memory.available),
            'used_gb': bytes_to_gb(memory.used),
            'percent_used': memory.percent
        }

    def _get_cpu_usage(self) -> Dict:
        """Get CPU usage statistics."""
        return {
            'usage_percent': psutil.cpu_percent(interval=1),
            'cores': psutil.cpu_count(logical=False),
            'threads': psutil.cpu_count(logical=True)
        }
