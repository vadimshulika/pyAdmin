"""File system operations handler for pyAdmin package."""

import shutil
import zipfile
import inspect
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

class FileManager:
    """Manage file system operations with path resolution and error handling.
    
    Provides methods for:
    - Copying/moving files with automatic directory creation
    - Creating ZIP archives
    - Retrieving file metadata
    - Path resolution relative to caller's directory
    """

    def __init__(self) -> None:
        """Initialize with caller's directory as base path.
        
        Example:
            >>> fm = FileManager()
        """
        frame = inspect.stack()[1]
        self.caller_dir = Path(frame.filename).parent.resolve()

    def _resolve_path(self, path: str) -> Path:
        """Convert relative path to absolute path relative to caller's directory.
        
        Args:
            path: Relative path string to resolve
            
        Returns:
            Path: Absolute Path object
            
        Example:
            >>> fm._resolve_path("data.txt")
            PosixPath('/home/user/project/data.txt')
        """
        return (self.caller_dir / path).resolve()

    def copy_file(self, source: str, destination: str) -> bool:
        """Copy file with full path resolution and error logging.
        
        Args:
            source: Relative path to source file
            destination: Relative destination path
            
        Returns:
            bool: True if copy succeeded, False otherwise
            
        Example:
            >>> fm.copy_file("config.yml", "backups/config_backup.yml")
            File /project/config.yml copied to /project/backups/config_backup.yml
            True
        """
        src = self._resolve_path(source)
        dest = self._resolve_path(destination)

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dest)
            print(f"File {src.name} copied to {dest}")
            return True
        except FileNotFoundError as e:
            print(f"Copy failed: {e.filename} not found")
        except PermissionError as e:
            print(f"Copy failed: Permission denied for {e.filename}")
        except Exception as e:
            print(f"Copy error: {str(e)}")
        return False

    def move_file(self, source: str, destination: str) -> bool:
        """Move file with automatic directory creation.
        
        Args:
            source: Relative path to source file
            destination: Relative destination path
            
        Returns:
            bool: True if move succeeded, False otherwise
            
        Example:
            >>> fm.move_file("temp.log", "logs/2023.log")
            File temp.log moved to logs/2023.log
            True
        """
        src = self._resolve_path(source)
        dest = self._resolve_path(destination)

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src, dest)
            print(f"File {src.name} moved to {dest}")
            return True
        except FileNotFoundError as e:
            print(f"Move failed: {e.filename} not found")
        except PermissionError as e:
            print(f"Move failed: Permission denied for {e.filename}")
        except Exception as e:
            print(f"Move error: {str(e)}")
        return False

    def compress_files(self, files: List[str], zip_name: str) -> bool:
        """Create ZIP archive with validation of source files.
        
        Args:
            files: List of relative file paths to compress
            zip_name: Name for output ZIP archive
            
        Returns:
            bool: True if archive created successfully
            
        Example:
            >>> fm.compress_files(["data.csv", "config.yml"], "backup.zip")
            Archive backup.zip created with 2 files
            True
        """
        zip_path = self._resolve_path(zip_name)
        added_files = 0

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in files:
                    file_path = self._resolve_path(file)
                    if file_path.is_file():
                        zipf.write(file_path, arcname=file_path.name)
                        added_files += 1
                    else:
                        print(f"Skipping {file_path}: Not a file")
            
            print(f"Archive {zip_path.name} created with {added_files} files")
            return added_files > 0
        except Exception as e:
            print(f"Compression failed: {str(e)}")
            return False

    def get_file_metadata(self, file_path: str) -> Dict[str, Optional[str]]:
        """Retrieve detailed metadata for specified file.
        
        Args:
            file_path: Relative path to target file
            
        Returns:
            Dict: Metadata dictionary with keys:
                - size_bytes: File size in bytes
                - creation_time: Creation date (DD.MM.YYYY)
                - modification_time: Last modified date (DD.MM.YYYY)
                - extension: File extension
                - permissions: Octal permissions string
                - absolute_path: Full path string
                
            Returns empty dict if file not found
            
        Example:
            >>> fm.get_file_metadata("readme.md")
            {
                'size_bytes': 2048,
                'creation_time': '15.07.2023',
                ...
            }
        """
        resolved_path = self._resolve_path(file_path)
        
        if not resolved_path.exists():
            print(f"File {resolved_path.name} not found")
            return {}

        try:
            stat = resolved_path.stat()
            return {
                'size_bytes': stat.st_size,
                'creation_time': datetime.fromtimestamp(stat.st_ctime).strftime("%d.%m.%Y"),
                'modification_time': datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y"),
                'extension': resolved_path.suffix,
                'permissions': oct(stat.st_mode)[-3:],
                'absolute_path': str(resolved_path.absolute())
            }
        except Exception as e:
            print(f"Metadata retrieval failed: {str(e)}")
            return {}