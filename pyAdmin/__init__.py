"""pyAdmin: A Python package for file management and system monitoring."""

from .file_manager import FileManager
from .system_monitoring import SystemMonitor
from .command_executor import CommandExecutor

version = "0.2.0"
all = ['FileManager', 'SystemMonitor', 'CommandExecutor']
