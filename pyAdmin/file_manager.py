import os
import shutil
import zipfile
from typing import List, Dict
from pathlib import Path
from pyAdmin.utils import bytes_to_gb

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class FileManager:
    """A class to manage files, directories, and system monitoring."""
    
    def copy_file(self, source: str, destination: str) -> bool:
        """
        Copy a file from source to destination.

        Args:
            source (str): Path to the source file.
            destination (str): Path to the destination.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            shutil.copy(source, destination)
            print(f"File {source} copied to {destination}")
            return True
        except Exception as e:
            print(f"Copy error: {str(e)}")
            return False

    def move_file(self, source: str, destination: str) -> bool:
        """
        Move a file from source to destination.

        Args:
            source (str): Path to the source file.
            destination (str): Path to the destination.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            shutil.move(source, destination)
            print(f"File {source} moved to {destination}")
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
        try:
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in files:
                    if Path(file).exists():
                        zipf.write(file, arcname=os.path.basename(file))
                    else:
                        print(f"Warning: {file} does not exist")
            print(f"Archive {zip_name} created successfully")
            return True
        except Exception as e:
            print(f"Compression error: {str(e)}")
            return False

    def get_system_status(self) -> Dict:
        """
        Get system resource usage (disk, memory, CPU).

        Returns:
            Dict: System status data or empty dict if psutil is not installed.
        """
        if not PSUTIL_AVAILABLE:
            print("psutil is required for this feature. Install it with 'pip install psutil'.")
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